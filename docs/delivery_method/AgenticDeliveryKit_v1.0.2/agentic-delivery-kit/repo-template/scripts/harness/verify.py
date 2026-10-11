#!/usr/bin/env python3
"""verify.py - one command that runs every computational sensor for this repository.

Agents and humans run exactly this to prove a change works:
    python scripts/harness/verify.py --fast   # inner loop: format, lint, types, unit tests
    python scripts/harness/verify.py          # full: everything in harness.toml (before "done", in CI)

Checks are defined in harness.toml ([[check]] tables). Output is short and LLM-friendly:
failing checks show the command, the tail of the output and a remediation hint.
On a local pass it writes .agent/verify-stamp.json, which the agent stop-guard hook reads.
Exit codes: 0 pass, 1 a check failed, 2 harness not configured.
Tier: STANDARD (kit-managed).
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    DEFAULT_NON_CODE_GLOBS, KIT_VERSION, changed_since, git, glob_match, is_placeholder, load_config, now_iso, repo_root,
    state_dir, tree_fingerprint, utf8_stdout, write_json,
)

TAIL_LINES = 40


def python_cmd() -> str:
    exe = sys.executable or "python"
    return f'"{exe}"' if os.name == "nt" else shlex.quote(exe)


def select_checks(cfg: dict, stage: str, only: list) -> list:
    checks = []
    for c in cfg.get("check", []) or []:
        if not isinstance(c, dict) or not c.get("name"):
            continue
        if c.get("enabled", True) is False:
            continue
        if only and c["name"] not in only:
            continue
        if stage == "fast" and not c.get("fast", False):
            continue
        checks.append(c)
    return checks


def run_check(root: Path, check: dict, changed: list) -> dict:
    name = check["name"]
    cmd = check.get("run_windows") if (os.name == "nt" and check.get("run_windows")) else check.get("run", "")
    result = {"name": name, "cmd": cmd, "status": "PASS", "seconds": 0.0, "tail": "", "hint": check.get("hint", "")}
    if is_placeholder(cmd):
        result.update(status="NOT CONFIGURED", tail="Set a real command for this check in harness.toml.")
        return result
    when = check.get("when")
    if when and changed is not None and not any(glob_match(p, when) for p in changed):
        result["status"] = "SKIP"
        result["tail"] = "No changed files match 'when' patterns."
        return result
    cmd = cmd.replace("{python}", python_cmd())
    timeout = int(check.get("timeout", 900))
    start = time.time()
    try:
        proc = subprocess.run(cmd, shell=True, cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=timeout)
        out = proc.stdout.decode("utf-8", errors="replace")
        code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b"").decode("utf-8", errors="replace") + f"\n[verify] TIMEOUT after {timeout}s"
        code = 124
    result["seconds"] = round(time.time() - start, 1)
    lines = out.rstrip().splitlines()
    result["tail"] = "\n".join(lines[-TAIL_LINES:])
    if code != 0:
        result["status"] = "WARN" if check.get("allow_failure") else "FAIL"
        result["exit"] = code
    return result


def render(results: list, stage: str, sha: str) -> str:
    lines = [f"# Verification evidence ({stage})", "", f"- When: {now_iso()}", f"- Commit: {sha}",
             f"- Harness kit: v{KIT_VERSION}", "", "| Check | Result | Time | Command |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['name']} | {r['status']} | {r['seconds']}s | `{r['cmd']}` |")
    for r in results:
        if r["status"] in ("FAIL", "NOT CONFIGURED", "WARN"):
            lines += ["", f"## {r['name']}: {r['status']}" + (f" (exit {r.get('exit')})" if r.get("exit") else ""),
                      "```text", r["tail"] or "(no output)", "```"]
            if r.get("hint"):
                lines.append(f"Hint: {r['hint']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    utf8_stdout()
    ap = argparse.ArgumentParser(description="Run the repository's computational sensors (see harness.toml).")
    ap.add_argument("--fast", action="store_true", help="only checks marked fast = true (inner loop)")
    ap.add_argument("--only", default="", help="comma-separated check names to run")
    ap.add_argument("--list", action="store_true", help="list configured checks and exit")
    ap.add_argument("--ci", action="store_true", help="CI mode: no local stamp, plain output")
    ap.add_argument("--fail-fast", action="store_true", help="stop at the first failing check")
    args = ap.parse_args()

    root = repo_root()
    cfg = load_config(root)
    if not cfg.get("check"):
        print("HARNESS NOT CONFIGURED: harness.toml with [[check]] entries is missing at the repository root.")
        print("Copy it from the Agentic Delivery Kit and set the real commands for this stack.")
        return 2
    stage = "fast" if args.fast else "full"
    only = [x.strip() for x in args.only.split(",") if x.strip()]
    checks = select_checks(cfg, stage, only)
    if args.list:
        for c in cfg.get("check", []):
            flag = "fast+full" if c.get("fast") else "full"
            print(f"- {c.get('name')}: [{flag}] {c.get('run', '')}")
        return 0
    if not checks:
        print(f"No checks selected for stage '{stage}'. Mark inner-loop checks with fast = true in harness.toml.")
        return 2

    changed = changed_since(root, None) if git(["rev-parse", "HEAD"], root) else None
    print(f"verify ({stage}) - {len(checks)} check(s)")
    results = []
    for check in checks:
        r = run_check(root, check, changed)
        results.append(r)
        print(f"  {r['status']:<14} {r['name']} ({r['seconds']}s)")
        if args.fail_fast and r["status"] in ("FAIL", "NOT CONFIGURED"):
            break

    failed = [r for r in results if r["status"] in ("FAIL", "NOT CONFIGURED")]
    for r in failed + [r for r in results if r["status"] == "WARN"]:
        print(f"\n--- {r['name']}: {r['status']} ---")
        print(f"command: {r['cmd']}")
        print(r["tail"] or "(no output)")
        if r.get("hint"):
            print(f"hint: {r['hint']}")

    sha = (git(["rev-parse", "--short", "HEAD"], root) or "no-git").strip()
    evidence = render(results, stage, sha)
    not_configured = [r for r in results if r["status"] == "NOT CONFIGURED"]
    if not args.ci:
        sd = state_dir(root)
        (sd / "last-verify.md").write_text(evidence, encoding="utf-8")
        write_json(sd / "verify-stamp.json", {
            "fingerprint": tree_fingerprint(root, (cfg.get("verify", {}) or {}).get("non_code_globs", DEFAULT_NON_CODE_GLOBS)), "stage": stage, "passed": not failed,
            "when": now_iso(), "commit": sha, "failed": [r["name"] for r in failed],
        })
    else:
        sd = state_dir(root)
        (sd / "last-verify.md").write_text(evidence, encoding="utf-8")

    print()
    if not_configured:
        print(f"RESULT: HARNESS NOT CONFIGURED ({', '.join(r['name'] for r in not_configured)}) - set real commands in harness.toml")
        return 2
    if failed:
        print(f"RESULT: FAIL - {len(failed)} of {len(results)} check(s) failed: {', '.join(r['name'] for r in failed)}")
        print("Fix the cause. Do not weaken, skip or delete tests to get green. Evidence: .agent/last-verify.md")
        return 1
    print(f"RESULT: PASS - {len(results)} check(s) ({stage}). Evidence: .agent/last-verify.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
