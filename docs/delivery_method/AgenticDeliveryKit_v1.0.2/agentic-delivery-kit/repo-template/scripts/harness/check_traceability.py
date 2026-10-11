#!/usr/bin/env python3
"""check_traceability.py - prove every requirement and acceptance scenario has a test.

Reads a Spec Kit feature spec (specs/<###-feature>/spec.md) and finds, in your test files,
references to each requirement ID:
    FR-###        functional requirements          (required)
    US<n>-AS<m>   acceptance scenario m of story n  (required; derived automatically from the
                  numbered **Given** lines under "### User Story n", or written explicitly)
    NFR-###, SC-### non-functional / success criteria (reported; add to [traceability] require)
    BR-###, DR-### ... any extra prefixes listed in harness.toml [traceability] id_prefixes
                  (e.g. business rules and data requirements from a PRD)
A test "covers" an ID when the ID text appears in it (test name, docstring, tag or a
"covers: FR-003" comment). FR_003 / us1_as2 spellings are accepted. Documentation files
(.md, .rst, .txt) are never evidence, even inside tests/.
Mark a requirement verified another way with "[VERIFY: manual]" (or inspection/analysis/demo)
on its line - it is listed, not failed; record the evidence in checks.md.

Scope is PROGRESSIVE by default - you must evidence what you claim is done:
  * scenarios of every user story that has at least one ticked [USn] task in tasks.md,
  * every ID mentioned in a ticked task line (e.g. "T014 [US1] unit tests for FR-002"),
  * everything, once all tasks in tasks.md are ticked (feature complete, gate G4).
No tasks.md yet (spec/plan stage) -> nothing is required. Use --strict to require everything now.

Usage:
    python scripts/harness/check_traceability.py                 # active feature (from branch name)
    python scripts/harness/check_traceability.py --feature specs/001-orders-export
    python scripts/harness/check_traceability.py --changed --base origin/main   # CI mode
    python scripts/harness/check_traceability.py --write         # also write <feature>/traceability.md
Exit codes: 0 covered (or not applicable), 1 gaps found.
Tier: STANDARD (kit-managed).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_NON_CODE_GLOBS, DEFAULT_TEST_GLOBS, SKIP_DIRS, changed_since, detect_feature_dir, glob_match, is_doc_file,
    load_config, repo_root, resolve_base, utf8_stdout,
)

VERIFY_TAG = re.compile(r"\[VERIFY:\s*(manual|inspection|analysis|demo)[^\]]*\]", re.I)
STORY_RX = re.compile(r"^#{2,4}\s+User Story\s+(\d+)\b", re.I)
SCENARIO_RX = re.compile(r"^\s*(\d+)\.\s+\*\*Given\*\*", re.I)
EXPLICIT_AS_RX = re.compile(r"\b(US\d+-AS\d+)\b")
DEFAULT_PREFIXES = ["FR", "NFR", "SC"]
REQ_RX = re.compile(r"\*\*((?:FR|NFR|SC)-\d+)\*\*")
TEST_ID_RX = re.compile(r"(?i)(?<![A-Za-z0-9])(?:(FR|NFR|SC)[-_ ]?0*(\d+)|US[-_ ]?(\d+)[-_ ]?AS[-_ ]?(\d+))(?![0-9])")


def configure_prefixes(prefixes) -> None:
    """Rebuild the ID patterns for the requirement prefixes this project uses (harness.toml)."""
    global REQ_RX, TEST_ID_RX
    clean = sorted({str(p).strip().upper() for p in prefixes if re.fullmatch(r"[A-Za-z]{1,6}", str(p).strip())},
                   key=lambda x: (-len(x), x))
    if not clean:
        clean = list(DEFAULT_PREFIXES)
    alt = "|".join(clean)
    REQ_RX = re.compile(r"\*\*((?:" + alt + r")-\d+)\*\*")
    TEST_ID_RX = re.compile(r"(?i)(?<![A-Za-z0-9])(?:(" + alt + r")[-_ ]?0*(\d+)|US[-_ ]?(\d+)[-_ ]?AS[-_ ]?(\d+))(?![0-9])")


def norm_req(kind: str, num: str) -> str:
    return f"{kind.upper()}-{int(num):03d}"


def strip_noise(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)       # template guidance comments
    text = re.sub(r"```.*?```", "", text, flags=re.S)        # fenced examples
    return text


def parse_spec(spec: Path) -> dict:
    """Return {id: {"type", "text", "manual"}} in document order."""
    items: dict = {}
    story = None
    for line in strip_noise(spec.read_text(encoding="utf-8", errors="replace")).splitlines():
        ms = STORY_RX.match(line)
        if ms:
            story = int(ms.group(1))
            continue
        if line.startswith("## "):
            story = None if not line.lower().startswith("## user scenarios") else story
        manual = bool(VERIFY_TAG.search(line))
        text = re.sub(r"\s+", " ", line.strip())[:110]
        for m in REQ_RX.finditer(line):
            rid = m.group(1)
            kind, num = rid.split("-", 1)
            rid = norm_req(kind, num)
            items.setdefault(rid, {"type": kind.upper(), "text": text, "manual": manual})
        explicit = EXPLICIT_AS_RX.findall(line)
        if explicit:
            for rid in explicit:
                s, a = re.match(r"US(\d+)-AS(\d+)", rid).groups()
                items.setdefault(f"US{int(s)}-AS{int(a)}", {"type": "AS", "text": text, "manual": manual})
            continue
        msc = SCENARIO_RX.match(line)
        if msc and story is not None:
            rid = f"US{story}-AS{int(msc.group(1))}"
            items.setdefault(rid, {"type": "AS", "text": text, "manual": manual})
    return items


TASK_LINE_RX = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(.*)$")
STORY_TAG_RX = re.compile(r"\[US(\d+)\]")


def task_scope(feature: Path, items: dict) -> tuple:
    """Return (required_ids or None for 'everything', description) from tasks.md progress."""
    tasks = feature / "tasks.md"
    if not tasks.exists():
        return set(), "no tasks.md yet - nothing required (spec/plan stage)"
    total, checked, started, claimed = 0, 0, set(), set()
    for line in strip_noise(tasks.read_text(encoding="utf-8", errors="replace")).splitlines():
        m = TASK_LINE_RX.match(line)
        if not m:
            continue
        total += 1
        if m.group(1).lower() != "x":
            continue
        checked += 1
        started.update(int(x) for x in STORY_TAG_RX.findall(line))
        for t in TEST_ID_RX.finditer(line):
            claimed.add(norm_req(t.group(1), t.group(2)) if t.group(1) else f"US{int(t.group(3))}-AS{int(t.group(4))}")
    if total and checked == total:
        return None, f"all {total} tasks ticked - feature complete, everything required"
    required = {rid for rid, info in items.items()
                if info["type"] == "AS" and int(re.match(r"US(\d+)", rid).group(1)) in started}
    required |= {rid for rid in claimed if rid in items}
    stories = ", ".join(f"US{n}" for n in sorted(started)) or "none"
    return required, f"progressive ({checked}/{total} tasks ticked; stories started: {stories})"


def iter_test_files(root: Path, globs: list):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".git")]
        for fn in filenames:
            full = Path(dirpath) / fn
            relp = full.relative_to(root).as_posix()
            if glob_match(relp, globs) and not is_doc_file(relp):
                yield full, relp


def scan_tests(root: Path, globs: list) -> dict:
    refs: dict = {}
    for full, relp in iter_test_files(root, globs):
        try:
            text = full.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in TEST_ID_RX.finditer(line):
                if m.group(1):
                    rid = norm_req(m.group(1), m.group(2))
                else:
                    rid = f"US{int(m.group(3))}-AS{int(m.group(4))}"
                refs.setdefault(rid, [])
                loc = f"{relp}:{lineno}"
                if loc not in refs[rid]:
                    refs[rid].append(loc)
    return refs


def report(feature: Path, root: Path, items: dict, refs: dict, required: set, scope) -> tuple:
    rows, missing, manual = [], [], []
    for rid, info in items.items():
        tests = refs.get(rid, [])
        if tests:
            status = "COVERED"
        elif info["manual"]:
            status = "MANUAL"
            manual.append(rid)
        elif info["type"] in required and (scope is None or rid in scope):
            status = "MISSING"
            missing.append(rid)
        elif info["type"] in required:
            status = "not yet due"
        else:
            status = "not required"
        shown = ", ".join(tests[:3]) + (f" (+{len(tests) - 3})" if len(tests) > 3 else "")
        rows.append(f"| {rid} | {info['type']} | {status} | {shown or '-'} |")
    rel_feature = feature.relative_to(root).as_posix()
    md = [f"# Traceability: {rel_feature}", "", "| ID | Type | Status | Tests |", "|---|---|---|---|", *rows, "",
          f"Required types: {', '.join(sorted(required))}. Missing: {len(missing)}. Manual: {len(manual)}."]
    return "\n".join(md) + "\n", missing, manual


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Requirement/scenario -> test traceability for Spec Kit features.")
    ap.add_argument("--feature", help="feature folder or spec.md (default: detect from branch)")
    ap.add_argument("--all", action="store_true", help="check every specs/*/spec.md")
    ap.add_argument("--changed", action="store_true", help="CI mode: only enforce when code (not just docs/specs) changed")
    ap.add_argument("--base", default=None, help="base ref for --changed (default origin/main)")
    ap.add_argument("--write", action="store_true", help="write traceability.md into the feature folder")
    ap.add_argument("--strict", action="store_true", help="require every ID now (ignore tasks.md progress)")
    args = ap.parse_args()

    root = repo_root()
    cfg = load_config(root)
    tcfg = cfg.get("traceability", {}) if isinstance(cfg.get("traceability"), dict) else {}
    test_globs = tcfg.get("test_globs") or (cfg.get("tests", {}) or {}).get("globs") or DEFAULT_TEST_GLOBS
    required = set(x.upper() for x in tcfg.get("require", ["FR", "AS"]))
    configure_prefixes(tcfg.get("id_prefixes", DEFAULT_PREFIXES) or DEFAULT_PREFIXES)

    features = []
    enforce = True
    if args.all:
        features = sorted(p.parent for p in (root / "specs").glob("*/spec.md"))
    else:
        if args.changed:
            base = resolve_base(root, args.base)
            changed = changed_since(root, base)
            non_code = (cfg.get("verify", {}) or {}).get("non_code_globs", DEFAULT_NON_CODE_GLOBS)
            code_changed = [p for p in changed if not glob_match(p, non_code) and not p.startswith(".github/")]
            for p in changed:
                parts = p.split("/")
                if len(parts) > 2 and parts[0] == "specs" and (root / "specs" / parts[1] / "spec.md").exists():
                    fp = root / "specs" / parts[1]
                    if fp not in features:
                        features.append(fp)
            if not code_changed:
                enforce = False
        active = detect_feature_dir(root, args.feature)
        if active and active not in features:
            features.append(active)

    if not features:
        print("traceability: no active Spec Kit feature found (chore/bug lane, or not on a ###-feature branch) - not applicable.")
        return 0

    refs = scan_tests(root, test_globs)
    total_missing = 0
    for feature in features:
        spec = feature / "spec.md"
        if not spec.exists():
            print(f"traceability: {feature.relative_to(root).as_posix()} has no spec.md - skipped.")
            continue
        items = parse_spec(spec)
        if not items:
            print(f"traceability: no FR-### or acceptance scenarios found in {spec.relative_to(root).as_posix()}.")
            continue
        scope, scope_text = (None, "strict - everything required") if args.strict else task_scope(feature, items)
        md, missing, manual = report(feature, root, items, refs, required, scope)
        md = md.rstrip("\n") + f"\nScope: {scope_text}.\n"
        print(md)
        if missing:
            print("MISSING means no test mentions the ID. Add a test that verifies it (put the ID in the test name or a")
            print("'covers: <ID>' comment), or mark the requirement [VERIFY: manual] and record evidence in checks.md.")
        if manual:
            print(f"Manual verification must be evidenced in {feature.relative_to(root).as_posix()}/checks.md: {', '.join(manual)}")
        if args.write:
            (feature / "traceability.md").write_text(md, encoding="utf-8")
        total_missing += len(missing)

    if total_missing and not enforce:
        print("Spec/docs-only change: gaps reported but not enforced.")
        return 0
    return 1 if total_missing else 0


if __name__ == "__main__":
    sys.exit(main())
