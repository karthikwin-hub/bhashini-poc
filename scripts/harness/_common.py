"""Shared helpers for the Agentic Delivery Standard harness scripts.

Stdlib only. Works on Windows, macOS and Linux with Python 3.9+
(Python 3.11+ is recommended: it reads harness.toml with the built-in tomllib).
Tier: STANDARD - managed by the kit; extend behaviour through harness.toml, not by editing.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

KIT_VERSION = "1.0.2"
STATE_DIR = ".agent"

# Paths that never need code verification (docs, specs, local agent state).
DEFAULT_NON_CODE_GLOBS = ["**/*.md", "docs/**", "specs/**", ".specify/**", ".agent/**"]

# Where tests usually live. Override in harness.toml -> [tests] globs.
DEFAULT_TEST_GLOBS = [
    "tests/**", "test/**", "**/__tests__/**", "**/*.test.*", "**/*.spec.*",
    "**/test_*.py", "**/*_test.py", "**/*_test.go", "**/*Test.java", "**/*Tests.java",
    "**/*Test.cs", "**/*Tests.cs", "**/*.feature",
]
DEFAULT_ACCEPTANCE_GLOBS = ["tests/acceptance/**"]

# Documentation is never test evidence, even inside a tests/ folder (e.g. tests/acceptance/README.md):
# an ID quoted in a README example must not count as a test that verifies it.
DOC_SUFFIXES = (".md", ".markdown", ".rst", ".txt", ".adoc")


def is_doc_file(path: str) -> bool:
    return path.replace("\\", "/").lower().endswith(DOC_SUFFIXES)

# Directories never scanned for tests or IDs.
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "dist", "build", "out", "target", "bin", "obj",
    ".specify", "specs", ".agent", "coverage", ".next", ".nuxt", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".gradle", ".idea", ".vscode",
}


def utf8_stdout() -> None:
    """Make printing safe on Windows consoles."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def git(args: List[str], cwd: Path, binary: bool = False, timeout: int = 60):
    """Run git; return stdout (str or bytes) or None if git fails or is missing."""
    try:
        res = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, timeout=timeout)
    except Exception:
        return None
    if res.returncode != 0:
        return None
    return res.stdout if binary else res.stdout.decode("utf-8", errors="replace")


def repo_root(start: Optional[Path] = None) -> Path:
    p = (start or Path.cwd()).resolve()
    top = git(["rev-parse", "--show-toplevel"], p)
    if top and top.strip():
        return Path(top.strip())
    for q in [p, *p.parents]:
        if (q / "harness.toml").exists() or (q / "AGENTS.md").exists():
            return q
    return p


def state_dir(root: Path) -> Path:
    d = root / STATE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_config(root: Path) -> dict:
    """Read harness.toml. Returns {} if missing or unreadable."""
    path = root / "harness.toml"
    if not path.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ModuleNotFoundError:  # pragma: no cover
        try:
            import tomli as tomllib  # type: ignore
        except ModuleNotFoundError:
            sys.stderr.write("[harness] Python 3.11+ (or the 'tomli' package) is needed to read harness.toml\n")
            return {}
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except Exception as exc:
        sys.stderr.write(f"[harness] harness.toml could not be parsed: {exc}\n")
        return {}


def _glob_to_regex(pattern: str) -> "re.Pattern[str]":
    pat = pattern.replace("\\", "/")
    if pat.startswith("./"):
        pat = pat[2:]
    out, i = [], 0
    while i < len(pat):
        ch = pat[i]
        if ch == "*":
            if pat[i:i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
                continue
            if pat[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$")


_GLOB_CACHE: dict = {}


def glob_match(path: str, patterns: Iterable[str]) -> bool:
    """gitignore-style matching: patterns without '/' match the file name anywhere."""
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    name = p.rsplit("/", 1)[-1]
    for pat in patterns:
        rx = _GLOB_CACHE.get(pat)
        if rx is None:
            rx = _GLOB_CACHE[pat] = _glob_to_regex(pat)
        if "/" not in pat.replace("\\", "/"):
            if rx.match(name) or rx.match(p):
                return True
        elif rx.match(p):
            return True
    return False


def rel(root: Path, path: str) -> str:
    """Repo-relative POSIX path when inside the repo, otherwise the normalised absolute path."""
    try:
        pp = Path(path)
        if not pp.is_absolute():
            pp = (root / pp)
        pp = pp.resolve()
        return pp.relative_to(root.resolve()).as_posix()
    except Exception:
        return path.replace("\\", "/")


def working_tree_changes(root: Path) -> List[str]:
    """Modified, staged and untracked files (respecting .gitignore)."""
    out = git(["status", "--porcelain=v1", "-uall"], root) or ""
    files = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:  # rename
            path = path.split(" -> ", 1)[1]
        files.append(path.strip().strip('"'))
    return files


def resolve_base(root: Path, base: Optional[str]) -> Optional[str]:
    """Return a usable base ref (given, origin/main, main, origin/master, master) or None."""
    candidates = [base] if base else []
    candidates += ["origin/main", "main", "origin/master", "master"]
    for ref in candidates:
        if ref and git(["rev-parse", "--verify", "--quiet", ref], root) is not None:
            return ref
    return None


def changed_since(root: Path, base: Optional[str]) -> List[str]:
    files = set(working_tree_changes(root))
    if base:
        diff = git(["diff", "--name-only", f"{base}...HEAD"], root) or ""
        files.update(x.strip() for x in diff.splitlines() if x.strip())
    return sorted(files)


def tree_fingerprint(root: Path, ignore_globs: Optional[Iterable[str]] = None) -> Optional[str]:
    """Hash of the effective content of every *code* file (HEAD tree + uncommitted changes).

    Files matching ignore_globs (docs, specs, agent state) are excluded, so updating progress.md
    or committing docs after a passing verify does not invalidate the verification.
    """
    ignore = list(ignore_globs if ignore_globs is not None else DEFAULT_NON_CODE_GLOBS)
    tree = git(["ls-tree", "-r", "HEAD"], root)
    if tree is None:
        return None
    entries = {}
    for line in tree.splitlines():
        try:
            meta, path = line.split("\t", 1)
        except ValueError:
            continue
        if not glob_match(path, ignore):
            entries[path] = meta.split()[-1]
    for path in working_tree_changes(root):
        if glob_match(path, ignore):
            continue
        fp = root / path
        if fp.is_file():
            try:
                entries[path] = hashlib.sha256(fp.read_bytes()).hexdigest()
            except Exception:
                entries[path] = "unreadable"
        else:
            entries.pop(path, None)
    h = hashlib.sha256()
    for path in sorted(entries):
        h.update(f"{path}\0{entries[path]}\n".encode("utf-8", "replace"))
    return h.hexdigest()


def current_branch(root: Path) -> Optional[str]:
    for env in ("GITHUB_HEAD_REF", "BUILD_SOURCEBRANCHNAME"):
        if os.environ.get(env):
            return os.environ[env]
    out = git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return out.strip() if out else None


def detect_feature_dir(root: Path, explicit: Optional[str] = None) -> Optional[Path]:
    """Find the active Spec Kit feature folder (specs/<###-name>/)."""
    specs = root / "specs"
    if explicit:
        p = Path(explicit)
        p = p if p.is_absolute() else root / p
        if p.is_file():
            p = p.parent
        return p if p.exists() else None
    if not specs.is_dir():
        return None
    for name in (os.environ.get("SPECIFY_FEATURE"), current_branch(root)):
        if not name:
            continue
        name = name.split("/")[-1]
        if (specs / name).is_dir():
            return specs / name
        m = re.match(r"^(\d{3,})-", name)
        if m:
            hits = sorted(specs.glob(f"{m.group(1)}-*"))
            if hits:
                return hits[0]
    return None


def is_placeholder(cmd: str) -> bool:
    return (not cmd) or cmd.strip().upper().startswith("TODO")
