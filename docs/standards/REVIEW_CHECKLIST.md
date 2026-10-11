# Review Checklist — for the reviewer agent and human reviewers

<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed) -->

Review the change **against intent** (spec.md, plan.md, the constitution), not against your own taste. Style and formatting
are the sensors' job — don't spend review time on them. Read the diff cold: you did not write it.

## Severity
- **BLOCKER** — wrong behaviour, data loss, security hole, broken contract, weakened test or acceptance criterion. Must fix.
- **MAJOR** — likely defect, missing test for a requirement, invariant violation (ownership, duplication, logic in UI), unhandled error path. Must fix or get an explicit human waiver.
- **MINOR** — maintainability or clarity issue with a concrete fix. Fix now or log as follow-up.
- **NIT** — optional. Keep these rare.

## 1. Intent and scope
- [ ] Every changed behaviour traces to an FR-### or US<n>-AS<m>; nothing was built that the spec didn't ask for.
- [ ] No acceptance scenario, requirement or existing acceptance test was changed without approval.
- [ ] No unrelated refactors, renames or dependency changes ride along.
## 2. Evidence
- [ ] `verify.py` (full) output is in the PR and passes; traceability shows no MISSING; /speckit.converge reports Converged.
- [ ] checks.md has a verdict and evidence for every requirement; manual verifications are actually evidenced.
## 3. Tests
- [ ] Tests assert behaviour, including negative and edge cases (empty, null, boundaries, duplicates, time zones, permissions).
- [ ] Tests would fail if the feature were removed (no tautologies, no asserting on mocks only).
- [ ] No new skips, `.only`, loosened assertions or broadened tolerances.
## 4. Design
- [ ] Logic lives in its owning module (docs/ARCHITECTURE.md); no duplicated rule, threshold, format or schema fact.
- [ ] No business logic in UI, templates, controllers or routes; domain code free of framework types.
- [ ] Simplest workable shape; no speculative abstraction; refactor and behaviour change are in separate commits.
## 5. Correctness and robustness
- [ ] Errors handled or propagated with context — none swallowed. Inputs validated at the boundary.
- [ ] Concurrency, idempotency and retries considered for integrations and messages.
- [ ] Data migrations are backward compatible or have a tested rollback.
## 6. Security
- [ ] No secrets or personal data in code, logs, tests or fixtures. Parameterised queries; output encoded.
- [ ] Authorisation enforced server-side; least privilege for any new credential or permission.
- [ ] New dependencies justified, from the official registry, licence acceptable.
## 7. Operability
- [ ] Structured logs with correlation IDs on new critical paths; useful error messages; metrics where the plan asked.
- [ ] Config via environment/config files, not hard-coded; feature flags have an owner and an expiry.
- [ ] Rollback is one command and is stated in the PR.

## Reviewer output format (agents)
```
Verdict: APPROVE | CHANGES REQUESTED
Findings:
1. [BLOCKER|MAJOR|MINOR|NIT] path:line — what is wrong — evidence (quote/command) — suggested fix
Not checked: <anything you could not verify, and why>
```
