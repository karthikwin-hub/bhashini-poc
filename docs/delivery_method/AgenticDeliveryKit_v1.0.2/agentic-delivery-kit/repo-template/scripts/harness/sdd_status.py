#!/usr/bin/env python3
"""sdd_status.py - where is the active feature? (tasks open/done, handoff present, evidence present)

    python scripts/harness/sdd_status.py              # active feature from branch name
    python scripts/harness/sdd_status.py --feature specs/001-orders-export
Exit codes: 0 all tasks checked, 1 open tasks remain (used by the agentic-sdd workflow), 2 no feature.
Tier: STANDARD (kit-managed).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import detect_feature_dir, repo_root, utf8_stdout  # noqa: E402

TASK_RX = re.compile(r"^\s*-\s*\[( |x|X)\]\s*(T\d+)?\s*(.*)$")


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Status of the active Spec Kit feature.")
    ap.add_argument("--feature", help="feature folder (default: detect from branch)")
    args = ap.parse_args()
    root = repo_root()
    feature = detect_feature_dir(root, args.feature)
    if not feature:
        print("sdd-status: no active feature folder (specs/<###-name>) detected.")
        return 2
    rel = feature.relative_to(root).as_posix()
    tasks = feature / "tasks.md"
    print(f"Feature: {rel}")
    for name in ("spec.md", "plan.md", "tasks.md", "progress.md", "checks.md", "traceability.md"):
        print(f"  {'present' if (feature / name).exists() else 'missing':<8} {name}")
    if not tasks.exists():
        print("No tasks.md yet - run /speckit.tasks.")
        return 1
    open_tasks, done = [], 0
    for line in tasks.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TASK_RX.match(line)
        if not m:
            continue
        if m.group(1).lower() == "x":
            done += 1
        else:
            open_tasks.append(f"{m.group(2) or '-'} {m.group(3)[:90]}")
    total = done + len(open_tasks)
    print(f"Tasks: {done}/{total} done")
    for t in open_tasks[:15]:
        print(f"  [ ] {t}")
    if len(open_tasks) > 15:
        print(f"  ... {len(open_tasks) - 15} more")
    return 1 if open_tasks else 0


if __name__ == "__main__":
    sys.exit(main())
