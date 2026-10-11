# Spec Kit preset: agentic-delivery

Layers the team's Agentic Delivery Standard onto Spec Kit's core Spec-Driven Development process **without forking it**.
It replaces the constitution scaffold and *appends* team sections and instructions to the core spec/plan templates and the
tasks/implement/converge commands, so upstream Spec Kit improvements keep flowing in.

| Component | Strategy | What it adds |
|---|---|---|
| constitution-template | replace | Ten articles (spec first, traceable evidence, verification before done, simplicity, ownership, security, observability, reversibility, human accountability, continuous harness improvement) + gates G1–G4 |
| spec-template | append | Scope boundaries, measurable NFRs, data/integration contracts, testing requirements (tests are requested), risks, G1 checklist |
| plan-template | append | Harness and verification plan, test design per story, ownership and dependencies, security, observability, rollout/rollback, agent execution notes, G2 checklist |
| speckit.tasks | append | Acceptance tests first (named by scenario ID), "Done when / Verify" on every task, refactor-first tasks, story checkpoints, final convergence and review tasks |
| speckit.implement | append | Session start protocol, per-task verify-tick-commit loop, protected contract, stop rules, story checkpoints, output contract |
| speckit.converge | append | Verify, traceability and checks.md are convergence evidence; no "Converged" while any disagree |

## Install (per repository)
```powershell
# after: specify init --here --integration copilot   (or claude)
specify preset add --dev <path-to-kit>/spec-kit/preset-agentic-delivery --priority 5
specify preset list
specify preset resolve spec-template      # shows core + this preset's addendum
```
Then run `/speckit.constitution` (or `/speckit-constitution` in skills mode) with your project's specifics — the command fills
the `[PLACEHOLDERS]` in the team constitution from repository evidence and your answers.

## Distribute to the whole team
Publish this folder (zip) with a catalog entry in an internal catalog and add it once per machine or project:
`specify preset catalog add <https-url-to-catalog.json> --name team --install-allowed`. See Spec Kit's preset docs for the
catalog format and `PUBLISHING.md`.

## Spec Kit versions
The preset declares `speckit_version >= 0.16.1` so it can be tried with the WBD golden template, which pins Spec Kit 0.16.1
(with the wbd-sdd extension). It was written against the Spec Kit 1.1 documentation. Validate it once on your version with
`specify preset resolve spec-template` and a throwaway spec before relying on it.

## Validate after Spec Kit upgrades
Spec Kit evolves quickly. After upgrading, run `specify preset resolve spec-template` and generate a throwaway spec/plan/tasks
in a scratch repo to confirm the appended sections still land where expected.
