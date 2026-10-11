## Scope Boundaries *(mandatory — Agentic Delivery Standard)*
<!-- ACTION REQUIRED: Make the edges explicit so agents do not over-deliver. -->
- **In scope**: [capabilities this feature delivers]
- **Out of scope**: [explicitly excluded — agents must not build these]
- **Must not change**: [existing behaviour, APIs, data or UX that must stay exactly as is — each one becomes a regression check]

## Non-Functional Requirements *(mandatory — measurable)*
<!-- ACTION REQUIRED: Numbers, not adjectives. Delete lines that genuinely do not apply; mark unknowns [NEEDS CLARIFICATION]. -->
- **NFR-001** Performance: [e.g. p95 response < 300 ms at 50 requests/s; batch of 10k rows < 2 s]
- **NFR-002** Security and privacy: [authorisation rule, data classification, audit requirement]
- **NFR-003** Reliability: [e.g. idempotent on retry; no data loss on restart; behaviour when upstream is down]
- **NFR-004** Observability: [events to log with correlation ID; metrics; alert conditions]
- **NFR-005** Accessibility / usability (UI): [e.g. WCAG 2.2 AA for new screens; keyboard operable]
- **NFR-006** Compatibility and data: [backward compatibility, retention, migration constraints]

## Data and Integration Contracts *(include if the feature touches data, APIs, messages or files)*
- **Inputs**: [source system, format/schema, frequency, volume]
- **Outputs**: [target system, format/schema, delivery guarantee]
- **Rules on failure**: [retries, idempotency key, dead-letter, partial data]
- **Examples**: [link or inline sample payloads — they become approved fixtures]

## Testing Requirements *(mandatory — tests ARE requested for this feature)*
- Every functional requirement (FR-###) and every acceptance scenario (US<n>-AS<m> = scenario m under User Story n) MUST be
  verified by an automated test that names its ID, or be marked `[VERIFY: manual]` with the reason and verified in checks.md.
- Acceptance tests for P1 stories are written from the scenarios **before implementation** and reviewed by the spec owner.
- Each "Must not change" item above gets a regression test. Complex outputs use human-approved fixtures.
- Test levels expected: [acceptance via API/UI | contract tests for each boundary | end-to-end for P1 journeys | performance for NFR-001]

## Risks, Assumptions and Open Questions
- [Risk or assumption — impact — how we will know — owner]

## Spec Quality Checklist — Gate G1 "Spec Ready"
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Each FR states one testable behaviour (MUST/SHOULD) with an ID; no implementation details
- [ ] Each user story has numbered Given/When/Then scenarios, including at least one negative or edge case
- [ ] Every FR is exercised by at least one scenario or has `[VERIFY: …]` with a reason
- [ ] NFRs are measurable; success criteria are measurable and technology-agnostic
- [ ] In scope / out of scope / must-not-change are explicit
- [ ] Spec owner approval: [name] on [date]
