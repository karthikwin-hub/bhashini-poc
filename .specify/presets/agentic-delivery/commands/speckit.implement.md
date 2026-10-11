
## Agentic Delivery Standard — implementation protocol (appended by preset `agentic-delivery`)

Follow AGENTS.md. In addition, while executing tasks.md:

1. **Session start** — read spec.md, plan.md, tasks.md and `progress.md` (create it from `docs/templates/progress-template.md`
   if missing) and `git log --oneline -15`. Run `python scripts/harness/verify.py --fast` as a baseline. If the baseline fails,
   stop and report — do not build on a red baseline.
2. **Scope of a session** — one user-story phase per session, in task order. Run `[P]` tasks in parallel only when they touch
   different files.
3. **Per task loop** — smallest change that satisfies the task → run its *Verify* command → read the output → fix the cause →
   tick the checkbox `[X]` → commit `<type>(<scope>): T0xx <summary>`.
4. **The contract is fixed** — do not modify acceptance scenarios in spec.md or existing acceptance tests. If one looks wrong or
   contradicts the plan, stop and record the question under "Open issues" in progress.md.
5. **Stop rules** — the same failure twice → stop, record what you tried, re-plan · a task needing changes outside its stated
   files or scope → stop and ask · three blocked tasks in a session → end the session with a report.
6. **Story checkpoint** — run full `python scripts/harness/verify.py` and `python scripts/harness/check_traceability.py`; update
   `checks.md` (requirement | verdict | evidence | correction) and progress.md (Completed, Decisions, Next action); commit.
7. **Report** with the AGENTS.md output contract. Never claim completion without the verify output from this session.
