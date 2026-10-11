---
name: refactor-safely
description: "Change structure without changing behaviour: consolidate duplicated logic into its owning module, then reuse it - in separate, verified commits. Use before adding a second use of existing logic, or when a task says refactor/move/extract."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Refactor safely (engineering invariants INV-2 and INV-4)

1. **Find every copy** — grep for the expression itself (the arithmetic, format string, threshold, regex), not just the
   function name. List each location.
2. **Pin current behaviour** — make sure tests cover each caller; for rule-heavy code capture an output dump
   (inputs → outputs) before you start.
3. **Move** the logic to its owning module (docs/ARCHITECTURE.md). Keep each caller's exact results — guards, rounding,
   clamps, time zones, null handling.
4. **Switch all callers** to the moved logic, or name in the commit message each copy left behind and why.
5. **Prove no behaviour change** — tests green, output dump identical. Commit: `refactor(<scope>): move X to <owner> (no behaviour change)`.
6. **Only then** make the behaviour change, in its own commit, with its own tests.

Never: a new helper beside the old copies (that's one more duplicate) · a refactor and a behaviour change in one diff ·
abstracting things that merely look alike but change for different reasons.
