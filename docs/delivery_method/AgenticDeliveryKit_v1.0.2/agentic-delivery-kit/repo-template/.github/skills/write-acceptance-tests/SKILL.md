---
name: write-acceptance-tests
description: "Derive executable acceptance tests from a spec's Given/When/Then scenarios, named with their US<n>-AS<m> IDs, before implementation. Use when starting a user story, when traceability reports MISSING scenarios, or when the test-designer role is invoked."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Acceptance tests from scenarios

1. **Read** the user story in `specs/<feature>/spec.md`, the test levels and contracts in plan.md, and
   `docs/standards/TESTING_STRATEGY.md`. Find the existing acceptance-test conventions in `tests/acceptance/`.
2. **One test per scenario**, ID first in the name: `US1-AS2: export excludes rows hidden by filters`.
   Scenario IDs come from the numbered **Given** lines under `### User Story n`.
3. **Given** → arrange state through public interfaces or fixtures · **When** → one action through the public interface
   (API call, UI step, CLI, message) · **Then** → assert the observable outcome, not internals.
4. **Edge and negative cases** the scenario implies get their own tests (same ID, suffix `-edge-…`).
5. **Complex outputs** (reports, payloads, transformations): use an approved fixture in `tests/fixtures/approved/`.
   You may *propose* the golden file; a human approves it.
6. **Determinism** — synthetic data, injected clock and seeds, no sleeps, no shared state between tests.
7. **Run them** — they must fail *for the right reason* (behaviour missing), not because of setup errors.
8. **Hand over** — list `test → scenario IDs` and ask the spec owner to confirm the tests express the intended behaviour
   (gate G3). After that, these tests are protected: implementation must not change them.
