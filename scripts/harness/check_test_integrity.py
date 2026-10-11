#!/usr/bin/env python3
"""check_test_integrity.py - stop a change from getting green by weakening the safety net.

Compares the branch with its base and flags:
  VIOLATION  a test file was deleted
  VIOLATION  a skip / focus / xfail marker was added to a test (.skip, xit, .only, @Disabled, ...)
  VIOLATION  an existing acceptance test was modified or deleted ([tests] acceptance_globs)
  VIOLATION  acceptance scenarios (**Given**) or requirements (**FR-###**) were removed/changed in a spec.md
  WARNING    a modified test file lost more assertions than it gained
Legitimate changes are allowed when a human approves them: set ALLOW_TEST_CHANGES=true
(CI maps the 'approved-test-change' PR label to it) or pass --allow.

Usage:
    python scripts/harness/check_test_integrity.py --base origin/main
Exit codes: 0 clean (or approved), 1 violations.
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
    DEFAULT_ACCEPTANCE_GLOBS, DEFAULT_TEST_GLOBS, git, glob_match, is_doc_file, load_config, repo_root, resolve_base,
    utf8_stdout,
)

SKIP_MARKERS = [
    r"\.skip\s*\(", r"\bx(it|describe|test)\s*\(", r"\.only\s*\(", r"\bf(it|describe)\s*\(",
    r"@pytest\.mark\.(skip|xfail)", r"\bpytest\.(skip|xfail)\s*\(", r"@unittest\.skip", r"@(Disabled|Ignore)\b",
    r"\[Ignore\]", r"\[(Fact|Theory)\s*\(\s*Skip\s*=", r"\bt\.Skip(Now)?\s*\(", r"\bskip\s*:\s*true\b",
    r"\btest\.todo\s*\(", r"@Tag\(\s*\"?flaky",
]
ASSERT_RX = re.compile(r"\b(assert\w*|expect\s*\(|Assert\.|should\b|verify\s*\(|assertThat)", re.I)
SKIP_RX = re.compile("|".join(SKIP_MARKERS))


def diff_name_status(root: Path, base: str | None) -> list:
    out = []
    if base:
        txt = git(["diff", "--name-status", "--find-renames", f"{base}...HEAD"], root) or ""
        out += [ln.split("\t") for ln in txt.splitlines() if ln.strip()]
    txt = git(["diff", "--name-status", "--find-renames", "HEAD"], root) or ""
    out += [ln.split("\t") for ln in txt.splitlines() if ln.strip()]
    return out


def file_patch(root: Path, base: str | None, path: str) -> str:
    parts = []
    if base:
        parts.append(git(["diff", "-U0", f"{base}...HEAD", "--", path], root) or "")
    parts.append(git(["diff", "-U0", "HEAD", "--", path], root) or "")
    return "\n".join(parts)


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Detect weakened tests or acceptance criteria.")
    ap.add_argument("--base", default=None, help="base ref (default: origin/main, main, ...)")
    ap.add_argument("--allow", action="store_true", help="human-approved test changes (same as ALLOW_TEST_CHANGES=true)")
    args = ap.parse_args()

    root = repo_root()
    cfg = load_config(root)
    tcfg = cfg.get("tests", {}) or {}
    test_globs = tcfg.get("globs") or DEFAULT_TEST_GLOBS
    acceptance_globs = tcfg.get("acceptance_globs") or DEFAULT_ACCEPTANCE_GLOBS
    allowed = args.allow or os.environ.get("ALLOW_TEST_CHANGES", "").strip().lower() in ("1", "true", "yes")

    base = resolve_base(root, args.base)
    if base is None:
        print("test-integrity: no base branch found (origin/main, main, ...); checking uncommitted changes only.")

    violations, warnings, seen = [], [], set()
    for entry in diff_name_status(root, base):
        status, paths = entry[0], entry[1:]
        path = paths[-1] if paths else ""
        key = (status[0], path)
        if not path or key in seen:
            continue
        seen.add(key)
        is_doc = is_doc_file(path)  # a README in tests/ documents the tests; it is not one
        is_test = glob_match(path, test_globs) and not is_doc
        is_acceptance = glob_match(path, acceptance_globs) and not is_doc
        if status.startswith("D") and is_test:
            violations.append(f"deleted test file: {path}")
            continue
        if status.startswith("R") and is_acceptance:
            violations.append(f"renamed/moved acceptance test: {paths[0]} -> {path}")
        if status.startswith("M") and is_acceptance:
            violations.append(f"modified existing acceptance test: {path}")
        if is_test and status[0] in "AMR":
            patch = file_patch(root, base, path)
            added = [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
            removed = [l[1:] for l in patch.splitlines() if l.startswith("-") and not l.startswith("---")]
            for line in added:
                if SKIP_RX.search(line):
                    violations.append(f"skip/focus marker added in {path}: {line.strip()[:90]}")
            if status[0] == "M":
                lost = sum(bool(ASSERT_RX.search(l)) for l in removed) - sum(bool(ASSERT_RX.search(l)) for l in added)
                if lost > 0:
                    warnings.append(f"{path}: {lost} fewer assertion line(s) than before - check nothing was weakened")
        if path.endswith("spec.md") and path.startswith("specs/") and status[0] == "M":
            patch = file_patch(root, base, path)
            removed = [l[1:] for l in patch.splitlines() if l.startswith("-") and not l.startswith("---")]
            for line in removed:
                if "**Given**" in line or re.search(r"\*\*[A-Z]{1,6}-\d+\*\*", line):
                    violations.append(f"acceptance scenario/requirement changed in {path}: {line.strip()[:90]}")

    for w in warnings:
        print(f"WARNING   {w}")
    for v in violations:
        print(f"VIOLATION {v}")
    if violations and allowed:
        print(f"test-integrity: {len(violations)} protected change(s) APPROVED by a human (ALLOW_TEST_CHANGES).")
        return 0
    if violations:
        print("\nThese changes can make a failing change look green. If they are intended, a human must approve them")
        print("(add the 'approved-test-change' label to the PR); otherwise fix the code, not the tests.")
        return 1
    print(f"test-integrity: OK (base: {base or 'working tree'}){' - with warnings' if warnings else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
