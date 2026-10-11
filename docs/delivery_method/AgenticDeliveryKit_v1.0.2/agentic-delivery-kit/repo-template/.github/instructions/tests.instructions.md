---
applyTo: "**/tests/**,**/test/**,**/__tests__/**,**/*.test.*,**/*.spec.*,**/test_*.py,**/*_test.py,**/*Test.java,**/*Tests.cs"
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD. Applies when Copilot works on test files. Full strategy: docs/standards/TESTING_STRATEGY.md -->
# Writing and changing tests
- Name the requirement or scenario the test proves: put `FR-###` or `US<n>-AS<m>` in the test name or a `covers:` comment.
- Test behaviour through public interfaces; assert outcomes, not implementation details. Include negative and edge cases.
- Mock only at system boundaries (network, clock, third parties). Inject clocks and seeds; no sleeps; no order dependence.
- Synthetic data only — never production or personal data.
- Never weaken, skip (`.skip`, `xit`, `@Disabled`, `[Ignore]`), focus (`.only`) or delete a test to get green. Existing acceptance
  tests in `tests/acceptance/` are the spec owner's contract: if one looks wrong, stop and ask.
- Bug fix: first add a test that reproduces the bug and fails for the right reason.
