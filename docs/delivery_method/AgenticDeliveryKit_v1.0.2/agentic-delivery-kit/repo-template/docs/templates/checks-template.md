# Checks — [###-feature-name]

<!-- Agentic Delivery Standard v1.0 · tier: STANDARD. Copy to specs/<feature>/checks.md. One row per requirement/scenario.
     Verdict: PASS | FAIL | UNRESOLVED. Evidence = test name + command result, file path, screenshot or reviewer note.
     Missing evidence stays visible as UNRESOLVED — never delete a row to look complete. -->

| Requirement | Verdict | Evidence | Correction / follow-up |
|---|---|---|---|
| FR-001 | PASS | `tests/unit/test_export.py::test_fr_001_only_visible_rows` · verify full PASS @ abc1234 | — |
| US1-AS1 | PASS | `tests/acceptance/export.spec.ts` "US1-AS1 …" · Playwright run 2026-10-08 | — |
| FR-003 [VERIFY: inspection] | PASS | Reviewer confirmed JSON response unchanged: contract test `contracts/orders.v1.json` | — |
| NFR-001 | UNRESOLVED | No load test yet | Add k6 test in follow-up issue #[n] |

## Independent review
- Reviewer: [agent name + model, or person] · Verdict: [APPROVE / CHANGES REQUESTED] · Findings resolved: [links]

## Convergence
- /speckit.converge: [Converged | N tasks appended] on [date]
