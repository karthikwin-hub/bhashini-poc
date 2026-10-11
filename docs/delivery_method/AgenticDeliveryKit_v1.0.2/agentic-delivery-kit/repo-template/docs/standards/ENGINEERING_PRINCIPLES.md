# Engineering Principles and Invariants

<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed — extend in docs/PROJECT_RULES.md instead of editing here) -->

These are constraints, not a checklist. When two conflict, choose the option with the **lowest future cost for this
repository** and say so in the commit message or PR description. AGENTS.md section 5 is the short, hard form of this page.

## 1. Design principles

| Principle | What it means here |
|---|---|
| Separation of concerns | Every file has one concern: domain rules · persistence · presentation · transport/routing · integration adapters. Name the concern of the file you edit; if you can't, it's doing too much. |
| Encapsulation | Use another module's public contract only. Read its data, caches and tables through its functions or API — never directly. |
| High cohesion, low coupling | One business-rule change touches one module. If a rule change ripples across many files, ownership is wrong. |
| DRY — with judgment | `grep` before writing logic. One home per rule, threshold, format or schema fact. Do **not** abstract coincidental similarity: two things that look alike but change for different reasons stay separate. |
| KISS / YAGNI | The simplest working shape. A function before a class. No speculative hooks, flags, plug-in points or frameworks. |
| Single responsibility | If you describe it with "and", split it. Names say intent; comments say *why*, never *what*. |
| Depend on contracts | Domain code takes and returns plain values and never imports web-framework, request, ORM-session or UI types. |
| Composition over inheritance | Inherit only for true "is-a" with shared invariants. |
| Open/closed — only where change has happened twice | Add extension points after the second real variation, not before. |
| Law of Demeter | No `a.b.c.d` reach-through; ask the owner. |
| Fail fast | Validate at the edges (API, message, file, user input). Never swallow errors; never return "success" from a failure path. |
| Optimise for deletion | Prefer code that is easy to remove: small modules, clear seams, feature flags with an expiry. |
| Boring technology | Prefer the stack and libraries already in the repo. New technology needs an ADR. |

## 2. Hard invariants (never violate)

### INV-1 One owning module per business domain
Each domain (e.g. pricing, scheduling rules, rights windows, media-asset requests, imports, reporting) lives in exactly one
module together with its rules document, listed in `docs/ARCHITECTURE.md` → *Domain ownership*. Everyone else calls it.
- Extend the owning module; create a new one only when you can state why the old one cannot own the rule.
- Consolidate a scattered domain **before** adding to it.
- A function-level import used to dodge a circular dependency means the logic is in the wrong module.

### INV-2 Never duplicate logic — move, switch, then reuse
On the second use of existing logic:
1. `grep` for the expression (the arithmetic, format string, threshold, regex) and list every copy.
2. Move it to the owner/shared module; switch **all** callers (or name in the commit each copy left and why).
3. Keep each caller's exact results (guards, rounding, clamps, time zones) — tests green, no behaviour change.
4. Only then build the new use, in a separate commit. Any behaviour change is its own commit.
A new helper written beside old copies is one more duplicate. The same applies to schemas (one fact, one column) and UI
(one component/partial per repeated piece).

### INV-3 No business logic in presentation or transport
Templates, UI components, client-side scripts, controllers/routes and view builders only display or route values. Arithmetic,
rules or classifications on business data there is a bug: move it to the owning module. *Who may see a value* is decided
server-side in the domain/authorisation layer, not by a template `if`.

### INV-4 Refactor first, then change
A behaviour-preserving refactor (tests green; for rule-heavy domains, compare an output dump before/after) is committed
**separately** from the behaviour change. Never both in one unverifiable diff.

### INV-5 Contracts at the boundaries
APIs, events/messages, file formats and schemas are versioned contracts with contract tests. Changes are backward compatible
unless the spec explicitly says otherwise and a migration path exists.

### INV-6 Errors are never silent
No empty `catch`/`except`, no blanket `except Exception: pass`, no ignored return codes. Log with context (correlation ID)
and either handle meaningfully or propagate.

## 3. Gates, not promises — how each invariant is enforced

A prompted "never" alone does not protect anything. A rule that matters is enforced by a check, a hook or CI.

| Invariant | Guide (feed-forward) | Sensor (feedback) — choose per stack | Runs |
|---|---|---|---|
| INV-1 ownership | ARCHITECTURE.md ownership table; plan.md "owning module" field | Architecture/dependency rules: dependency-cruiser (JS/TS), import-linter (Python), ArchUnit (Java), NetArchTest / ArchUnitNET (.NET) | verify (full), CI |
| INV-2 duplication | `refactor-safely` skill | Duplicate-code detector: jscpd, PMD CPD, pylint `duplicate-code`; weekly scan loop | CI, weekly |
| INV-3 presentation | path-specific instructions for UI/route folders | Dependency rule "presentation must not import domain calculators directly" + review checklist item | verify (full), review |
| INV-4 refactor first | AGENTS.md §3; tasks.md refactor tasks first | Reviewer agent flags mixed refactor + behaviour diffs; PR size budget | review |
| INV-5 contracts | contracts/ in plan; skill `write-acceptance-tests` | Contract tests (schema validation, consumer-driven contracts) | verify (full), CI |
| INV-6 silent errors | AGENTS.md §5 | Lint: ESLint `no-empty`, Ruff `S110`/`BLE001`/`E722`, CA1031 (.NET), PMD `EmptyCatchBlock` | verify (fast) |

A rule that matters and has no sensor yet goes into `docs/agent-memory/harness-backlog.md` until it has one.
