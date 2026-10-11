# Definition of Done

<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed) -->

"Done" is a claim backed by evidence. If the evidence isn't there, the item is not done — whoever (or whatever) did the work.

## Task done (one line in tasks.md)
- [ ] The change does exactly what the task says, touching only the files it names (or the deviation is explained).
- [ ] Its Verify command ran and passed (default `python scripts/harness/verify.py --fast`); output was read, not assumed.
- [ ] Checkbox ticked, committed with a conventional message referencing the task (`feat(orders): T014 add CSV export endpoint`).

## User story done (end of a tasks.md phase)
- [ ] All story tasks ticked; acceptance tests for every scenario of the story pass.
- [ ] Full `python scripts/harness/verify.py` passes; `check_traceability.py` shows no MISSING for the story.
- [ ] checks.md rows for the story have a verdict and evidence; progress.md "Next action" is current.
- [ ] The story works on its own (independently testable and demonstrable, as the spec requires).

## Feature done (gate G4)
- [ ] /speckit.converge reports **Converged**; no open tasks (`sdd_status.py` exits 0).
- [ ] Independent review (reviewer agent with fresh context and/or a human) — no unresolved BLOCKER/MAJOR findings.
- [ ] NFRs verified or explicitly evidenced (performance, security, accessibility as specified).
- [ ] Docs updated: ARCHITECTURE.md if structure changed, ADR for significant decisions, runbook/README for operators.
- [ ] PR description follows the output contract, includes evidence and AI-assistance disclosure, and states the rollback.
- [ ] Lessons from corrections captured as candidates in `docs/agent-memory/lessons.md`.

## Released
- [ ] Merged by a human after required checks and CODEOWNERS reviews.
- [ ] Deployed by the pipeline (not by an agent); post-release checks/monitors green; spec owner accepts the outcome.
