---
name: reproduce-bug
description: "Fix a bug the reliable way: reproduce it with a failing test first, find the root cause, make the smallest fix, and re-run the original steps. Use for any defect report, failing behaviour or production incident follow-up."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Reproduce, then fix

Tracked bug with Spec Kit? Prefer the bundled process: `/speckit-bug-assess` → `/speckit-bug-fix` → `/speckit-bug-test`
(`specify extension add bug`). This skill is the same discipline for quick fixes.

1. **Get the steps** — exact input, environment, expected vs actual. Missing? Ask for them; don't guess.
2. **Reproduce** — run the steps. Cannot reproduce → stop and say what you need (data, logs, environment, version).
3. **Capture it in a test** — the smallest test that fails *because of the bug* (check the failure message proves it).
   Name it after the issue (`bug-1234: …`).
4. **Find the root cause** — trace the call path (use the explorer role); fix the cause, not the symptom. Never silence
   an error or add a special case for the failing input only.
5. **Fix minimally** — smallest change in the owning module (AGENTS.md §5). No drive-by refactors.
6. **Prove it** — the new test passes; re-run the original reproduction steps; `python scripts/harness/verify.py` passes.
7. **Look sideways** — the same faulty pattern elsewhere? List the locations under *Skipped* (or fix if the task says so).
8. **Report** — the output contract, including cause, fix and evidence. If the bug came from a missing rule, propose a lesson.
