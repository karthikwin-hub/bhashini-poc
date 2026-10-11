
## Agentic Delivery Standard — convergence evidence (appended by preset `agentic-delivery`)

In addition to comparing the codebase with spec.md, plan.md and tasks.md, treat these as convergence evidence:

- Run `python scripts/harness/verify.py` (full). Any failing check is a gap → append a task to fix it.
- Run `python scripts/harness/check_traceability.py --strict --write`. Every MISSING requirement or scenario is a gap → append
  a test task naming the ID.
- Read `checks.md`: every requirement without a PASS verdict and observed evidence is a gap.
- A ticked task with no corresponding commit or verify evidence is not complete — re-open it.
- Open issues in progress.md that affect requirements block convergence until a human resolves them.

Report **Converged** only when verify passes, traceability (strict) has no MISSING items, checks.md has PASS for every
requirement (or an approved [VERIFY: manual] result), and no requirement-affecting issue is open. Otherwise report
**Not converged — N tasks appended**, with the evidence table.
