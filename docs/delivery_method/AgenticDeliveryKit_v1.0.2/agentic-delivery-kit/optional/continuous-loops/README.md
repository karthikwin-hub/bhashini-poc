# Continuous loops — agents that work between features

<!-- Agentic Delivery Standard v1.0 · optional. Start report-only; earn write access with evidence. -->

A loop is a system that prompts the agent for you: **trigger → goal → verifier → stop rules → budget → state → escalation**.
These four loops pay back fastest for a team. Build them with **GitHub Agentic Workflows** (`gh aw`, Markdown workflows that
run in GitHub Actions, read-only by default, writing only through validated "safe outputs"), Copilot/Claude scheduled tasks,
or a plain scheduled CI job.

## Rules for every loop
1. **Week 1–2 report-only**: the loop opens an issue or comment; it changes nothing. Promote to draft PRs only when its
   reports are consistently right.
2. **A verifier that is not the model's opinion**: exit codes, test results, diff size limits, a separate reviewer.
3. **Two budgets, always**: max iterations/runs and max tokens or cost per run. A loop without budgets is unsupervised, not autonomous.
4. **Durable state outside the model**: an issue label, a state file or a tracking issue, so it never re-does handled work.
5. **Escalation by design**: on failure, stop, keep the evidence, notify the owner with enough context to act.
6. **Least privilege**: read-only agent; writes only via safe outputs (issue, comment, draft PR); a human merges.

## Loop cards

| Loop | Trigger | Goal | Verifier | Stop / budget | Output (safe) | Owner |
|---|---|---|---|---|---|---|
| **CI doctor** | CI run on main fails | Diagnose the failure; propose a fix | Fix PR must pass Quality Gates | 1 run per failure; 1 PR max; 30 min | Issue with diagnosis → later a draft PR | Tech lead |
| **Docs gardener** | Weekly (Mon 06:00) | Find docs/ARCHITECTURE/README statements that no longer match the code | Each claim cites file:line on both sides | ≤ 5 findings per run | Issue → later one draft PR | Harness steward |
| **Golden-principles sweep** | Weekly | Find violations of ENGINEERING_PRINCIPLES (duplication, logic in UI, swallowed errors) | Duplicate detector / architecture rules confirm each finding | ≤ 3 findings; small fixes only | Issue → later small draft PRs ("garbage collection") | Harness steward |
| **Test improver** | Weekly | Add tests where mutation or coverage reports show weak protection of core domain code | New tests pass; mutation score rises; no production code changed | ≤ 1 PR per run | Draft PR | QA / dev lead |

## Creating them with GitHub Agentic Workflows
Install once: `gh extension install github/gh-aw`, then `gh aw init` in the repository. Then paste a prompt like this into your
coding agent (the official authoring path — the agent writes and compiles the workflow for you to review):

> Create a workflow for GitHub Agentic Workflows using https://raw.githubusercontent.com/github/gh-aw/main/create.md.
> The purpose of the workflow is a weekly **docs gardener**: compare docs/ARCHITECTURE.md, README.md and docs/standards with
> the code; report up to 5 statements that are now wrong, each with file:line evidence on both sides. Read-only. Output one
> GitHub issue labelled `agentic,docs` via safe-outputs create-issue. Do not create pull requests.

Repeat with the CI doctor (trigger: workflow_run failure of "Quality Gates" on main; output: issue with diagnosis), the
golden-principles sweep, and the test improver. Review the generated `.github/workflows/*.md` and `.lock.yml`, then commit.
Ready-made workflows (CI Doctor, Repo Assist, Daily Test Improver) are also available from the gh-aw catalogue.

## Measure each loop
Runs · useful findings (accepted by a human) · false positives · cost per run · time-to-fix for what it found. Retire a loop
whose findings are ignored for a month.
