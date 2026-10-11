<!-- Agentic Delivery Standard v1.0 · PR template. Agents fill this from the AGENTS.md output contract. Reviewers: review intent and
     evidence first (docs/standards/REVIEW_CHECKLIST.md); style is the sensors' job. -->

## Summary
**Lane**: chore | bug | small change | feature   ·   **Spec**: `specs/###-feature/spec.md` (or issue #)
One or two sentences: what this delivers and why.

## Needs from reviewer
1. <!-- most blocking first, or "Nothing" -->

## What changed
- `path/file` — one line each

## Evidence
- `python scripts/harness/verify.py` (full): PASS / FAIL — summary of `.agent/last-verify.md`
- Traceability: N/N requirements and scenarios covered (MANUAL: …)
- /speckit.converge: Converged · Independent review: APPROVE (who/which agent)
- UI checked in a browser (if applicable): what was tried

## Skipped / not verified
-

## Blocked
-

## Rollback
`git revert <sha>` <!-- plus any data/migration rollback step -->

## New rule / lesson
- none <!-- or link to the candidate in docs/agent-memory/lessons.md -->

## AI assistance disclosure
- Tool(s) and mode: <!-- e.g. Copilot coding agent; Claude Code (plan mode → auto-edit in devcontainer) -->
- Model(s): <!-- e.g. ... -->
- Extent: <!-- e.g. agent wrote all code and tests; human wrote spec and reviewed acceptance tests -->

## Reviewer checklist
- [ ] Behaviour matches spec; nothing extra; no acceptance criteria or acceptance tests weakened
- [ ] Evidence present and green; traceability complete
- [ ] Logic in its owning module; no duplication; no business logic in UI/controllers
- [ ] Security, error handling and rollback acceptable
