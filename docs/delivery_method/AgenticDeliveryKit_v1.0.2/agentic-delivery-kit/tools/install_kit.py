#!/usr/bin/env python3
"""install_kit.py - install or update the Agentic Delivery Standard in a repository.

    python tools/install_kit.py <repo>                    # first install (never overwrites existing files)
    python tools/install_kit.py <repo> --tools copilot    # only Copilot files (or: claude, both - default)
    python tools/install_kit.py <repo> --update           # refresh STANDARD files to this kit version
    python tools/install_kit.py <repo> --dry-run          # show what would happen

Tiers (kit-manifest.json):
  STANDARD - kit-managed (scripts/harness, docs/standards, agents, skills, hooks, instructions). Same in every repo;
             --update overwrites them. Extend through project files instead of editing them.
  SEED     - copied once, then project-owned (AGENTS.md, harness.toml, ARCHITECTURE.md, CI, CODEOWNERS ...). Never
             overwritten; on --update the newer kit version is written to .agent/kit-update/ for you to compare.
The target must be a clean git working tree (so the install is one reviewable diff) unless --force is given.
Stdlib only; Python 3.9+.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
TEMPLATE = KIT / "repo-template"


def git_dirty(target: Path) -> bool | None:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=target, capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return bool(out.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="Install/update the Agentic Delivery Standard into a repository.")
    ap.add_argument("target", help="path to the repository root")
    ap.add_argument("--tools", choices=["both", "copilot", "claude"], default="both")
    ap.add_argument("--update", action="store_true", help="overwrite STANDARD files with this kit version")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="allow a dirty working tree")
    args = ap.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"Target {target} does not exist.")
        return 2
    manifest = json.loads((KIT / "kit-manifest.json").read_text(encoding="utf-8"))
    dirty = git_dirty(target)
    if dirty is None:
        print("WARNING: target is not a git repository - the install will not be a reviewable diff.")
    elif dirty and not args.force and not args.dry_run:
        print("Target has uncommitted changes. Commit or stash them first (or use --force) so the install is one reviewable diff.")
        return 2

    counts: dict = {}
    lines = []
    for entry in manifest["files"]:
        if args.tools != "both" and entry["tool"] not in ("any", args.tools):
            continue
        src = TEMPLATE / entry["path"]
        dst = target / entry["path"]
        if not dst.exists():
            action = "added"
            if not args.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        elif dst.read_bytes() == src.read_bytes():
            action = "unchanged"
        elif entry["tier"] == "standard":
            if args.update:
                action = "updated"
                if not args.dry_run:
                    shutil.copy2(src, dst)
            else:
                action = "differs (use --update)"
        else:
            # SEED file already exists (project-owned, or created by another tool such as `specify init`):
            # never overwrite - leave the kit version beside it for a manual merge.
            action = "kept; kit copy in .agent/kit-update/ to merge"
            if not args.dry_run:
                side = target / ".agent" / "kit-update" / entry["path"]
                side.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, side)
        counts[action] = counts.get(action, 0) + 1
        if action != "unchanged":
            lines.append(f"  {action:<42} [{entry['tier']}] {entry['path']}")

    gi = target / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""
    wanted = [".agent/", "CLAUDE.local.md", ".claude/settings.local.json"]
    missing = [w for w in wanted if w not in existing.splitlines()]
    if missing and not args.dry_run:
        with gi.open("a", encoding="utf-8") as fh:
            fh.write(("\n" if existing and not existing.endswith("\n") else "") +
                     "# Agentic Delivery Standard - local agent state and personal settings\n" + "\n".join(missing) + "\n")
    if missing:
        lines.append(f"  {'gitignore':<42} added: {', '.join(missing)}")
    if not args.dry_run:
        (target / ".agentic-kit-version").write_text(
            f"version={manifest['version']}\ninstalled={date.today().isoformat()}\ntools={args.tools}\n", encoding="utf-8")

    print(f"Agentic Delivery Kit v{manifest['version']} -> {target}{'  (dry run)' if args.dry_run else ''}")
    print("\n".join(lines) if lines else "  nothing to change")
    print("Summary: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    preset = KIT / "spec-kit" / "preset-agentic-delivery"
    if (target / ".specify").is_dir():
        speckit = (f"  2. Team preset (once per repo):  specify preset add --dev \"{preset}\" --priority 5\n"
                   "     then in your agent:  /speckit.constitution <your project's real, agreed principles>")
    else:
        speckit = ("  2. Spec Kit is not initialised here. Run on a clean commit:\n"
                   "       specify init --here --force --integration copilot --script ps     (or: --integration claude / --script sh)\n"
                   "     then re-run this installer (it merges safely), then:\n"
                   f"       specify preset add --dev \"{preset}\" --priority 5   and   /speckit.constitution <principles>")
    print("\nNext steps\n"
          "  1. Fill the SEED files: AGENTS.md sections 1-2, harness.toml commands, docs/ARCHITECTURE.md, .github/CODEOWNERS.\n"
          "     Merge anything listed under .agent/kit-update/ by hand.\n"
          f"{speckit}\n"
          "  3. Readiness:  python scripts/harness/harness_doctor.py     Sensors:  python scripts/harness/verify.py\n"
          "  4. Commit on a branch and open a PR - harness files are reviewed like code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
