## Harness and Verification Plan *(mandatory — Agentic Delivery Standard)*
<!-- ACTION REQUIRED: This section tells the agents HOW they will prove the work. Use real commands from harness.toml. -->

### Verification commands
- Inner loop: `python scripts/harness/verify.py --fast` · Before done and in CI: `python scripts/harness/verify.py`
- Feature-specific checks to add to harness.toml (if any): [e.g. contract test suite, approved-fixture comparison, k6 smoke]

### Test design per user story
| Story | Acceptance tests (level · location) | Unit focus (FR-###) | Contract / integration | UI / E2E | Approved fixtures |
|---|---|---|---|---|---|
| US1 (P1) | [API acceptance · tests/acceptance/…] | [FR-001, FR-002] | [orders API v1 contract] | [Playwright: export journey] | [sample CSV] |

### Ownership and reuse (engineering invariants INV-1 / INV-2)
- Owning module for each business rule touched: [rule → module (docs/ARCHITECTURE.md)]
- Existing code reused: [functions/modules found by exploration]
- Consolidation needed first (refactor-before-change tasks): [duplicated logic to move, or "none"]
- New modules (with the reason an existing owner cannot hold the rule): [none / …]

### Dependencies
- New dependencies: **none** / [package — why existing options are insufficient — licence — approved by]

### Architecture fitness
- Dependency rules affected or added: [e.g. ui may not import domain/pricing]
- Performance / reliability checks for NFRs: [how each NFR is measured]

### Security and privacy
- Threats considered (spoofing, tampering, information disclosure, denial of service, elevation): [notes]
- Data classification and handling: [what data, where stored/logged, masking]
- Secrets and permissions needed: [none / which, least privilege]

### Observability
- Logs (with correlation ID), metrics, alerts added: [list] · How to diagnose a failure in production: [steps]

### Rollout and rollback
- Feature flag: [name, default, owner, removal date] / none
- Migration plan and backward compatibility: [steps]
- Rollback: [one command or procedure, incl. data]

### Agent execution notes
- Session plan: one user story per session, in priority order; [P] tasks only where files do not overlap
- Context to load first: [files/docs] · Files that must not be touched: [list]
- Known traps for agents in this area: [e.g. time-zone handling in scheduling; idempotency keys]

### Gate G2 — "Design Ready"
- [ ] Constitution Check passes (or deviations justified in Complexity Tracking)
- [ ] Contracts, data model and test design cover every FR and scenario
- [ ] Owning modules identified; reuse preferred; no unjustified new dependency
- [ ] Security, observability, rollout and rollback addressed
- [ ] Tech lead approval: [name] on [date]
