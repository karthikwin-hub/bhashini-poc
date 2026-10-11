# Agentic Delivery Kit — v1.0.2

A standard, reusable **harness** for AI-led software development with GitHub Spec Kit, GitHub Copilot and Claude Code.
It turns the playbook ("AI-Led Software Development Playbook") into files you drop into any repository:
guides that steer agents *before* they act, sensors that check their work *after* they act, guardrails that keep humans in
charge of irreversible decisions, and a Spec Kit preset + workflow that put quality gates into the delivery process.

> **Humans steer · agents execute · sensors decide · humans accept.**
> Spec it → Harness it → Loop it → Graph it → Steer it.

## What's inside
```text
agentic-delivery-kit/
├── README.md · QUICK_REFERENCE.md · CHANGELOG.md · kit-manifest.json
├── playbook/PLAYBOOK.md (+ img/)     # the full playbook in Markdown - the process, the why, roles, metrics, rollout
├── tools/install_kit.py                 # install / update the standard in a repo (tier-aware, never clobbers project files)
├── repo-template/                       # what gets copied into a repository
│   ├── AGENTS.md                        # SEED  the agents' map: workflow, scope guard, invariants, gates, output contract
│   ├── CLAUDE.md                        # SEED  imports @AGENTS.md for Claude Code
│   ├── harness.toml                     # SEED  this repo's sensors (fast + full) and agent policy
│   ├── .github/copilot-instructions.md  # SEED  short pointer for Copilot surfaces that don't read AGENTS.md
│   ├── .github/agents/*.agent.md        # STD   roles: explorer, implementer, test-designer, reviewer, verifier, harness-steward
│   ├── .github/skills/*/SKILL.md        # STD   procedures: verify-change, reproduce-bug, write-acceptance-tests,
│   │                                    #       refactor-safely, session-handoff, capture-lesson
│   ├── .github/instructions/*.md        # STD   path-specific rules for tests and specs
│   ├── .github/hooks/agent-guardrails.json  # STD  Copilot hooks: pre-tool guard, session start, verify-on-stop
│   ├── .github/workflows/quality-gates.yml  # SEED CI: verify, traceability, test integrity, secrets, dependency review
│   ├── .github/workflows/copilot-setup-steps.yml  # SEED toolchain for the Copilot cloud agent, so it can run verify.py
│   ├── .github/pull_request_template.md · .github/CODEOWNERS   # SEED
│   ├── .claude/settings.json · .claude/agents/ · .claude/skills/  # Claude Code equivalents
│   ├── scripts/harness/                 # STD   verify.py · check_traceability.py · check_test_integrity.py
│   │                                    #       agent_hooks.py · harness_doctor.py · sdd_status.py (stdlib Python)
│   └── docs/
│       ├── standards/                   # STD   ENGINEERING_PRINCIPLES · TESTING_STRATEGY · SECURITY_FOR_AGENTS
│       │                                #       REVIEW_CHECKLIST · DEFINITION_OF_DONE
│       ├── templates/                   # STD   progress (handoff) and checks (evidence) templates
│       ├── ARCHITECTURE.md · PROJECT_RULES.md · decisions/0000-adr-template.md       # SEED
│       └── agent-memory/lessons.md · harness-backlog.md                             # SEED
├── spec-kit/
│   ├── preset-agentic-delivery/         # Spec Kit preset: constitution + spec/plan addenda + tasks/implement/converge rules
│   └── workflows/agentic-sdd/           # Spec Kit workflow: the Lane 3 delivery graph with gates G1–G4
└── optional/continuous-loops/           # loop cards + creation prompts for scheduled/event agent loops (gh aw)
```

## Customisation model — standard everywhere, specific where it matters
| Tier | Files | Who owns them | How they change |
|---|---|---|---|
| **STANDARD** | `scripts/harness`, `docs/standards`, `docs/templates`, role agents, skills, instructions, hooks config, the preset | The kit (harness stewards) | New kit version → `install_kit.py --update`. Don't edit in a repo — extend instead. |
| **SEED** | AGENTS.md, CLAUDE.md, harness.toml, ARCHITECTURE.md, PROJECT_RULES.md, CI, CODEOWNERS, PR template, lessons | The project | Copied once, then yours. On `--update` the newer kit copy goes to `.agent/kit-update/` to compare. |
| **Nested / local** | `AGENTS.md` inside a package or folder; `.github/instructions/*.instructions.md` with `applyTo`; `CLAUDE.local.md` (personal, git-ignored) | Module owners / individuals | Add as needed; the nearest AGENTS.md wins for files beneath it. |
| **Spec Kit layer** | constitution (via `/speckit.constitution`); project-local overrides in `.specify/templates/overrides/` | The project | Constitution amendments by PR; one-off template tweaks as overrides — not edits to the preset. |

Project-specific additions go into SEED files (`docs/PROJECT_RULES.md`, `harness.toml` `[agent_policy]`, nested AGENTS.md),
so a kit update never fights your customisations.

## Quick start (Windows PowerShell; macOS/Linux use the same commands with `python3`)
Prerequisites: Git, Python 3.11+, `uv`, and GitHub Copilot and/or Claude Code. (Spec Kit itself needs Python 3.11+ and uv.)
```powershell
# 0. Spec Kit CLI (once per machine)
uv tool install specify-cli

# 1. Spec Kit first, on a clean branch (it creates .specify/ and the agent skill files)
cd C:\path\to\repo ; git switch -c chore/agentic-harness
specify init --here --force --integration copilot --script ps   # or --integration claude ; --force is needed in a non-empty repo
git add -A ; git commit -m "chore: initialise Spec Kit"

# 2. The kit, then the team preset and the bug/assess extensions
python <kit>\tools\install_kit.py .                          # --tools copilot | claude to install one side only
specify preset add --dev <kit>\spec-kit\preset-agentic-delivery --priority 5
specify extension add bug ; specify extension add assess       # lanes 1 and 4

# 3. Make it real (the part only your team can do)
#    - harness.toml: real format / lint / typecheck / unit / acceptance / architecture commands
#    - AGENTS.md sections 1-2, docs/ARCHITECTURE.md (domain ownership!), .github/CODEOWNERS handles
#    - in your agent: /speckit.constitution  <your project's real, agreed principles>
python scripts\harness\harness_doctor.py                       # until no FAIL
python scripts\harness\verify.py                               # must pass on a clean tree

# 4. Commit, open a PR, make "Quality Gates" a required check and enable "Require review from Code Owners".
```
Command names: this kit writes Spec Kit commands in command form (`/speckit.plan`). In skills mode (GitHub Copilot's default
in current Spec Kit, and the `-` separator used by the WBD golden template) type `/speckit-plan`: same command. Scripted or CI
set-ups add `--non-interactive` to `specify init` so it never waits on a picker.

Existing (brownfield) repository: same steps. Follow Spec Kit's existing-project guidance — capture only principles that are
already true or explicitly agreed, start with one bounded change (not "document the whole system"), and make the harness green
on the current code before agents start building.

## Day to day
See `QUICK_REFERENCE.md`. In short: pick the lane → for features run the Spec Kit flow (or `specify workflow run
spec-kit/workflows/agentic-sdd/workflow.yml -i spec="…"`) → agents implement one user story per session in the verify loop →
`/speckit.converge` until Converged → independent review → checks.md → human gate → PR.

## Roll it out in a week (one file written in one sitting is a file nobody follows)
| Day | Install | Prove it |
|---|---|---|
| 1 | AGENTS.md sections 1–6 and 10 (map, commands, workflow, scope, invariants, verification, gates) + constitution | An agent restates a task and stops at a gate |
| 2 | harness.toml with real commands; `verify.py` green; output contract | An agent reports evidence from `verify.py` |
| 3 | Hooks (Copilot and/or Claude) + CODEOWNERS + CI Quality Gates as required checks | Try `git push --force` and a test skip: both are blocked |
| 4 | Role agents and skills; one Lane 2 change end to end with the preset | Traceability and checks.md complete |
| 5 | Lessons file in use; first weekly harness review | One correction promoted — ideally to a check |

## Keeping the standard consistent across projects
- Keep this kit in one internal Git repository; tag versions (`v1.0.0`). Changes to STANDARD files go through review there.
- Projects run `python <kit>/tools/install_kit.py . --update` on a branch and review the diff like any change.
- Publish the preset and workflow through an internal Spec Kit catalog (`specify preset catalog add <url> --name team
  --install-allowed`; same for workflows) so `specify preset add agentic-delivery` works everywhere.
- `harness_doctor.py` gives every repo the same readiness score — use it in onboarding and quarterly reviews.

## Troubleshooting
- **Hooks don't fire (Copilot)**: the hooks file must be valid JSON on the default branch for the cloud agent; `bash` entries
  run on Linux/macOS and the cloud agent, `powershell` entries on Windows — `python`/`python3` must be on PATH.
- **Hooks don't fire (Claude Code)**: commands use `uv run`; check `uv --version`. Use `/hooks` to inspect, `/permissions` for rules.
- **A guard is too strict for your project**: tune `harness.toml` → `[agent_policy]`; don't edit `agent_hooks.py`.
  Guard errors fail *open* by design — CI and review remain the backstop.
- **Spec Kit wants to update AGENTS.md or copilot-instructions.md** (agent-context updates during `/speckit.plan`): the guard asks
  for approval because these are protected files. Approve if the change is confined to Spec Kit's marked block; AGENTS.md
  stays the canonical map.
- **A SEED file already existed** (e.g. created by `specify init`): the installer never overwrites it; merge the kit version
  from `.agent/kit-update/` by hand.
- **"NOT CONFIGURED"** from verify: a check still has `TODO` — set a real command or `enabled = false`.
- **Traceability MISSING**: put the ID (`FR-003`, `US1-AS2`) in the test name or a `covers:` comment, or mark the requirement
  `[VERIFY: manual]` with evidence in checks.md.

## Validation status
- The Python harness scripts were exercised against sample repositories (verify pass/fail/not-configured paths, progressive and
  strict traceability, test-integrity violations and approval, 60 guardrail decisions in Copilot and Claude payload formats,
  verify-on-stop guard, installer install/idempotency/update).
- The Spec Kit preset and workflow follow the Spec Kit 1.1 documentation (preset composition strategies, workflow step types).
  Validate them once in a scratch repo with `specify preset resolve spec-template` and `specify workflow info` before team
  rollout, and again after Spec Kit upgrades — Spec Kit ships changes weekly.
- Hook formats follow the current GitHub Copilot hooks reference and Claude Code hook conventions; confirm in your versions.
