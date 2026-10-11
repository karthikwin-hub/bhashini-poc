---
name: verify-change
description: "Prove a code change works before calling it done: run the harness checks, read failures, fix root causes and record evidence. Use after editing code, before committing, and before reporting any task as complete."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Verify a change

1. **Inner loop** — after each meaningful edit: `python scripts/harness/verify.py --fast` (format, lint, types, unit tests).
2. **Read the result.** For each FAIL read the command, the output tail and the hint. Fix the *cause*:
   - a failing test is information — fix the code, not the test (unless you can show the test is wrong; then ask);
   - never add skips, `.only`, broader tolerances or deleted assertions to get green.
3. **Same failure twice?** Stop. Write what you tried in progress.md and re-plan or ask.
4. **Before "done"** — `python scripts/harness/verify.py` (full: acceptance, contracts, architecture rules, traceability,
   test integrity). All must pass. `NOT CONFIGURED` means the harness needs a human — report it, don't work around it.
5. **UI changes** — run the journey in a browser; try to break it: empty input, double submit, refresh, back button, slow network.
6. **Evidence** — summarise `.agent/last-verify.md` under *Evidence* in the output contract: which checks, PASS/FAIL, commit.

Not verification: "it should work", a build that compiles, tests you didn't run, output from an earlier commit,
or a passing run after you changed the tests.
