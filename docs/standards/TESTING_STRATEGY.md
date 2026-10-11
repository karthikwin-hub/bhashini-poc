# Testing Strategy — the behaviour harness

<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed). Project thresholds live in the constitution and harness.toml. -->

Tests are the executable form of the spec. They are how an agent *proves* "done", and how a human trusts it without reading
every line. Linters and type checkers catch structural problems; **only tests and acceptance evidence catch wrong behaviour.**

## 1. Who writes what

| Artefact | Written by | Reviewed by | Rule |
|---|---|---|---|
| Acceptance scenarios (Given/When/Then in spec.md) | Spec owner (BA/product), with the agent's help | Spec owner + tech lead at gate G1 | The contract. Agents never change them without approval. |
| Acceptance tests (one per scenario, named with its ID) | `test-designer` agent, **before** implementation | Spec owner skims intent at gate G3 (mandatory for P1 stories) | Must fail first for the right reason; protected once merged. |
| Unit and integration tests | `implementer` agent, alongside the code | Reviewer agent + human PR review | Judged by outcomes (mutation score, changed-line coverage), not by ritual. |
| Contract tests (APIs, messages, files) | `implementer` / `test-designer` | Owning team of the other side | Required for every boundary in contracts/. |
| Approved fixtures (golden outputs) | Agent proposes | **A human approves every fixture diff** | Never auto-approved by an agent. |
| Bug reproduction test | Agent, first step of every bug fix | Reviewer | Must fail before the fix and pass after. |

Evidence note: asking an agent to run red-green TDD *inside its own loop* has not shown a reliable quality gain, while
human-authored or human-reviewed tests do act as an independent specification. So we put the human checkpoint on the
acceptance tests and measure unit-test quality by outcomes (mutation testing), rather than prescribing the ritual.

## 2. Traceability IDs (checked by `scripts/harness/check_traceability.py`)
- `FR-###` functional requirement · `US<n>-AS<m>` scenario *m* of user story *n* (derived from the numbered **Given** lines)
  · `NFR-###` non-functional requirement · `SC-###` success criterion.
- Put the ID in the test: in the name (`test("US1-AS2: rejects an empty title")`, `def test_fr_003_rejects_duplicate()`), a
  docstring, a tag/category, or a `covers: FR-003` comment.
- Requirements verified another way carry `[VERIFY: manual]` (or inspection / analysis / demo) and need evidence in `checks.md`.

## 3. The portfolio

| Level | Purpose | Where | When it runs |
|---|---|---|---|
| Unit | Domain rules and edge cases, fast and deterministic | next to code or `tests/unit/` | every change (`verify --fast`) |
| Acceptance | Each Given/When/Then scenario end-to-end through the public interface | `tests/acceptance/` | before "done", CI |
| Contract | Every API/message/file boundary in `contracts/` | `tests/contract/` | before "done", CI |
| Integration | Real database, queue, filesystem adapters (containers where possible) | `tests/integration/` | before "done", CI |
| UI / E2E | P1 user journeys in a real browser (e.g. Playwright) — agents must actually exercise the UI | `tests/e2e/` | CI; nightly for the full set |
| Approved fixtures | Complex outputs (reports, payloads, transformations) compared with a human-approved golden file | `tests/fixtures/approved/` | before "done", CI |
| Mutation | Do the tests catch injected faults? (Stryker, PIT, mutmut) | core domain modules | weekly / nightly |
| Non-functional | Performance, load, security, accessibility as the NFRs demand | `tests/perf`, scanners | nightly or per release |

## 4. Quality bars (defaults — set project values in the constitution)
- Changed-line coverage ≥ 80% (measured, not a target to game). Core-domain mutation score ≥ 70%, tracked weekly.
- No test is skipped without a linked issue and an owner; skips and `.only` are blocked by `check_test_integrity.py`.
- Flaky tests are quarantined within one working day with an issue; never "fixed" by retries alone.

## 5. Rules for agents (enforced by hooks and CI where possible)
1. A failing test is information. Fix the code, not the test — unless you can show the test is wrong, then ask.
2. Never weaken, skip, delete or loosen assertions or acceptance criteria to get green.
3. Test behaviour through public interfaces; don't assert on private implementation details.
4. Mock only at system boundaries (network, clock, third-party services); keep mocks honest with contract tests.
5. Deterministic: inject clocks and random seeds; no `sleep`; no dependency on test order or the developer's machine.
6. Synthetic test data only — no production data or personal information in tests or fixtures.
7. Every bug fix starts with a test that reproduces it.
8. UI changes: run the journey in a browser and try to break it (empty input, double submit, refresh, back button).
