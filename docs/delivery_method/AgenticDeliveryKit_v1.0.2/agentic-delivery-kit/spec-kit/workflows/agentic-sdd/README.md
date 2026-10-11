# Spec Kit workflow: agentic-sdd (the delivery graph)

A resumable Spec Kit workflow that encodes the Lane 3 delivery graph: agent nodes (commands and role prompts), deterministic
nodes (shell checks), human gates G1–G4, and one bounded retry branch after convergence.

```text
specify → clarify → [G1] → plan → checklist → [G2] → tasks → analyze → acceptance tests (test-designer) → [G3]
→ implement → verify → converge → open tasks? ──yes──► implement → verify → converge   (max one automatic second pass)
                                     │no
                                     ▼
independent review (fresh context) → verification report (checks.md) → status → [G4] → PR (human merges)
```

## Use
```powershell
specify workflow run <kit>/spec-kit/workflows/agentic-sdd/workflow.yml -i spec="Add CSV export to the orders page ..."
specify workflow status            # see where a run is paused
specify workflow resume <run_id>   # after you have reviewed the gate
```
Or install it once per project: `specify workflow add --dev <kit>/spec-kit/workflows/agentic-sdd`.

## Notes
- Requires the `agentic-delivery` preset and the repo template (scripts/harness) in the project; shell steps use `uv`, a Spec
  Kit prerequisite, so they work on Windows, macOS and Linux.
- Gates pause the run; nothing proceeds without a human. Rejecting aborts — fix the artefact and start a new run, or continue
  manually with the individual `/speckit.*` commands.
- Validate after Spec Kit upgrades: `specify workflow info ./workflow.yml`. Workflow syntax is evolving; this file uses only
  documented step types (command, prompt, shell, gate, if) and options.
- Smaller changes (Lane 2) don't need the workflow: run `/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
  → /speckit.converge` by hand.
