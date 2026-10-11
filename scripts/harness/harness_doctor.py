#!/usr/bin/env python3
"""harness_doctor.py - is this repository ready for agents? (a "harnessability" check)

    python scripts/harness/harness_doctor.py

Checks the guides (AGENTS.md, constitution, standards), the sensors (harness.toml commands,
tests, CI), the guardrails (hooks, CODEOWNERS, .gitignore) and the Spec Kit setup, and prints a
readiness score with the fix for each gap. Exit 1 if any FAIL.
Tier: STANDARD (kit-managed).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import DEFAULT_TEST_GLOBS, KIT_VERSION, glob_match, is_placeholder, load_config, repo_root, utf8_stdout  # noqa: E402
from check_traceability import iter_test_files  # noqa: E402

results = []


def check(status: str, area: str, msg: str, fix: str = "") -> None:
    results.append((status, area, msg, fix))


def main() -> int:
    utf8_stdout()
    root = repo_root()
    cfg = load_config(root)

    # Guides -----------------------------------------------------------------------------
    agents = root / "AGENTS.md"
    if not agents.exists():
        check("FAIL", "guides", "AGENTS.md missing", "Install the kit (tools/install_kit.py) or create AGENTS.md from the template.")
    else:
        text = agents.read_text(encoding="utf-8", errors="replace")
        n = len(text.splitlines())
        if n > 300:
            check("FAIL", "guides", f"AGENTS.md is {n} lines - it is a map, not a manual", "Move detail into docs/ and link to it (target <= 150 lines).")
        elif n > 150:
            check("WARN", "guides", f"AGENTS.md is {n} lines (target <= 150)", "Move detail into docs/ and link to it.")
        else:
            check("PASS", "guides", f"AGENTS.md present ({n} lines)")
        if "[e.g." in text or "[one sentence" in text:
            check("WARN", "guides", "AGENTS.md still has template placeholders", "Fill in section 1 (project map) and section 2 (real commands).")
    claude = root / "CLAUDE.md"
    if claude.exists() and "@AGENTS.md" not in claude.read_text(encoding="utf-8", errors="replace"):
        check("WARN", "guides", "CLAUDE.md does not import @AGENTS.md", "Add '@AGENTS.md' so Claude Code reads the shared rules.")
    if not (root / ".github" / "copilot-instructions.md").exists():
        check("WARN", "guides", ".github/copilot-instructions.md missing", "Copilot Chat on github.com reads only this file; add the kit's short pointer version.")
    for doc in ("ENGINEERING_PRINCIPLES.md", "TESTING_STRATEGY.md", "SECURITY_FOR_AGENTS.md", "REVIEW_CHECKLIST.md", "DEFINITION_OF_DONE.md"):
        if not (root / "docs" / "standards" / doc).exists():
            check("WARN", "guides", f"docs/standards/{doc} missing", "Re-run tools/install_kit.py --update.")
    arch = root / "docs" / "ARCHITECTURE.md"
    if not arch.exists():
        check("WARN", "guides", "docs/ARCHITECTURE.md missing", "Agents need the module-ownership map to put logic in the right place.")
    elif "[" in arch.read_text(encoding="utf-8", errors="replace")[:4000] and "CUSTOMIZE" in arch.read_text(encoding="utf-8", errors="replace"):
        check("WARN", "guides", "docs/ARCHITECTURE.md still has template placeholders", "Fill the domain ownership table and dependency rules.")
    else:
        check("PASS", "guides", "docs/ARCHITECTURE.md present")

    # Spec Kit ----------------------------------------------------------------------------
    specify = root / ".specify"
    if not specify.is_dir():
        check("WARN", "spec-kit", "Spec Kit not initialised", "Run: specify init --here --integration <copilot|claude> (see kit README).")
    else:
        if (specify / "templates").is_dir() or (specify / "scripts").is_dir():
            check("PASS", "spec-kit", "Spec Kit initialised")
        else:
            check("WARN", "spec-kit", "Spec Kit not initialised (.specify/ holds only memory files)",
                  "Run: specify init --here --force --integration <copilot|claude> on a clean commit, then restore your constitution.")
        const = specify / "memory" / "constitution.md"
        const_text = const.read_text(encoding="utf-8", errors="replace") if const.exists() else ""
        if not const.exists():
            check("FAIL", "spec-kit", "constitution.md missing", "Run /speckit.constitution with the team's agreed principles.")
        elif re.search(r"\[(PROJECT_NAME|PRINCIPLE_\d|CONSTITUTION_VERSION)\]", const_text):
            check("WARN", "spec-kit", "constitution has unfilled placeholders (not ratified)", "Run /speckit.constitution and approve it.")
        elif re.search(r"\*\*Ratified\*\*:\s*(pending|todo|tbd|\[)", const_text, re.I):
            check("WARN", "spec-kit", "constitution is a draft (not ratified yet)", "Review it with /speckit.constitution; record the ratification date when approved.")
        else:
            check("PASS", "spec-kit", "constitution ratified")
        if (specify / "presets" / "agentic-delivery").is_dir():
            check("PASS", "spec-kit", "agentic-delivery preset installed")
        else:
            check("WARN", "spec-kit", "agentic-delivery preset not installed", "specify preset add --dev <kit>/spec-kit/preset-agentic-delivery")

    # Sensors -----------------------------------------------------------------------------
    checks = cfg.get("check", []) or []
    if not checks:
        check("FAIL", "sensors", "harness.toml missing or has no [[check]] entries", "Copy harness.toml from the kit and set real commands.")
    else:
        todo = [c.get("name") for c in checks if c.get("enabled", True) is not False and is_placeholder(c.get("run", ""))]
        fast = [c for c in checks if c.get("fast")]
        if todo:
            check("FAIL", "sensors", f"harness.toml has unconfigured checks: {', '.join(todo)}", "Replace TODO with the real command, or set enabled = false.")
        else:
            check("PASS", "sensors", f"harness.toml: {len(checks)} checks configured ({len(fast)} fast)")
        if not fast:
            check("WARN", "sensors", "no fast checks", "Mark format/lint/types/unit tests with fast = true for the inner loop.")
    tests = list(iter_test_files(root, (cfg.get("tests", {}) or {}).get("globs") or DEFAULT_TEST_GLOBS))
    if tests:
        check("PASS", "sensors", f"{len(tests)} test file(s) found")
    else:
        check("WARN", "sensors", "no test files found", "Agents cannot prove behaviour without tests; start with acceptance tests for P1 journeys.")
    wf = root / ".github" / "workflows"
    ci_text = "".join(p.read_text(encoding="utf-8", errors="replace") for p in wf.glob("*.y*ml")) if wf.is_dir() else ""
    if "verify.py" in ci_text:
        check("PASS", "sensors", "CI runs verify.py")
    else:
        check("WARN", "sensors", "no CI workflow runs scripts/harness/verify.py", "Add .github/workflows/quality-gates.yml (or the equivalent in your CI).")

    # Guardrails --------------------------------------------------------------------------
    gi = root / ".gitignore"
    if gi.exists() and re.search(r"(?m)^/?\.agent/?\s*$", gi.read_text(encoding="utf-8", errors="replace")):
        check("PASS", "guardrails", ".agent/ is git-ignored")
    else:
        check("FAIL", "guardrails", ".agent/ not in .gitignore", "Add a line '.agent/' (local agent state and evidence).")
    hooks_ok = False
    for hf in (root / ".github" / "hooks").glob("*.json") if (root / ".github" / "hooks").is_dir() else []:
        try:
            data = json.loads(hf.read_text(encoding="utf-8"))
            hooks_ok = hooks_ok or "agent_hooks.py" in json.dumps(data)
        except Exception:
            check("FAIL", "guardrails", f"{hf.relative_to(root).as_posix()} is not valid JSON", "Fix the JSON; an invalid file disables all hooks in it.")
    cs = root / ".claude" / "settings.json"
    if cs.exists():
        try:
            hooks_ok = hooks_ok or "agent_hooks.py" in json.dumps(json.loads(cs.read_text(encoding="utf-8")))
        except Exception:
            check("FAIL", "guardrails", ".claude/settings.json is not valid JSON", "Fix the JSON.")
    if hooks_ok:
        check("PASS", "guardrails", "agent hooks configured (pre-tool guard, verify-on-stop)")
    else:
        check("WARN", "guardrails", "no agent hooks configured", "Install .github/hooks/agent-guardrails.json and/or .claude/settings.json from the kit.")
    owners = [p for p in (root / "CODEOWNERS", root / ".github" / "CODEOWNERS", root / "docs" / "CODEOWNERS") if p.exists()]
    if owners and "AGENTS.md" in owners[0].read_text(encoding="utf-8", errors="replace"):
        check("PASS", "guardrails", "CODEOWNERS protects harness files")
    else:
        check("WARN", "guardrails", "CODEOWNERS missing or does not cover AGENTS.md / harness files", "Use the kit's CODEOWNERS and enable 'Require review from Code Owners'.")
    if (root / ".github" / "pull_request_template.md").exists():
        check("PASS", "guardrails", "PR template present (output contract + AI disclosure)")
    else:
        check("WARN", "guardrails", "PR template missing", "Add .github/pull_request_template.md from the kit.")
    if not (root / "docs" / "agent-memory" / "lessons.md").exists():
        check("WARN", "learning", "docs/agent-memory/lessons.md missing", "Corrections need a home; add it from the kit.")

    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    print(f"Harness doctor (kit v{KIT_VERSION}) - {root}")
    for status, area, msg, fix in sorted(results, key=lambda r: (order[r[0]], r[1])):
        print(f"  {status:<4} [{area}] {msg}")
        if fix and status != "PASS":
            print(f"       fix: {fix}")
    passed = sum(1 for r in results if r[0] == "PASS")
    fails = sum(1 for r in results if r[0] == "FAIL")
    print(f"\nReadiness: {passed}/{len(results)} checks pass, {fails} fail(s).")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
