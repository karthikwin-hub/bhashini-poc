---
applyTo: "specs/**,.specify/**"
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD. Applies when Copilot works on Spec Kit artefacts. -->
# Working on specifications
- spec.md describes WHAT and WHY in business language — no technology, frameworks or code. plan.md holds the HOW.
- Every functional requirement is one testable behaviour using MUST/SHOULD, with an ID (`FR-###`). Mark unknowns
  `[NEEDS CLARIFICATION: question]` — never guess silently.
- Every user story has numbered **Given/When/Then** scenarios, including at least one negative or edge case. Scenario IDs are
  `US<story>-AS<number>`.
- NFRs are measurable (numbers, percentiles, limits). Success criteria are technology-agnostic and measurable.
- After G1 approval, acceptance scenarios and requirements change only with the spec owner's approval: propose the change
  in progress.md "Open issues" instead of editing.
- Keep artefacts consistent: if a discovery changes intent, update spec.md first, then plan.md and tasks.md, then run /speckit.analyze.
