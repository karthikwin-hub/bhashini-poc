
## Agentic Delivery Standard — task generation rules (appended by preset `agentic-delivery`)

Apply these rules in addition to the instructions above. They take precedence where they are stricter.

1. **Tests are requested** for every feature under this standard (constitution Article II). For each user story phase,
   generate test tasks *before* its implementation tasks:
   - one acceptance-test task per scenario, named with its ID, e.g.
     `T010 [P] [US1] Acceptance test US1-AS1 "export returns only visible rows" in tests/acceptance/export.spec.ts`;
   - unit-test tasks for the story's domain rules, naming the requirement IDs they prove (e.g. `… unit tests for FR-002 …`);
   - contract-test tasks for every contract in contracts/ that the story touches.
2. **Every task line ends with** ` — Done when: <observable condition> — Verify: <command>`.
   Default verify command: `python scripts/harness/verify.py --fast`.
3. **Refactor first**: if a story needs existing logic moved or consolidated (engineering invariant INV-2), create a separate
   refactor task *before* the behaviour change, with "no behaviour change" in its Done-when.
4. **Story checkpoint**: end each user-story phase with
   `TXXX [USn] Checkpoint: run python scripts/harness/verify.py and python scripts/harness/check_traceability.py; update checks.md and progress.md; commit`.
5. **Final phase must include**: run /speckit.converge until it reports Converged · independent review by the reviewer agent in
   a fresh context, findings resolved · docs/ADR/ARCHITECTURE.md updates · PR description using the AGENTS.md output contract.
6. Keep tasks small (one concern, roughly an hour of agent work), with exact file paths. Mark `[P]` only when the files do not overlap.
7. Every FR-### and US<n>-AS<m> in spec.md must appear in at least one task. List any that do not, instead of silently dropping them.
