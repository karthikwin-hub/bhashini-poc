# Changelog

## 1.0.2 — 2026-10-09
- Traceability and readiness: documentation files (.md, .rst, .txt) are never counted as tests, even inside `tests/`.
  Before this fix an ID quoted in `tests/acceptance/README.md` counted as test evidence (found in the pilot trial run).
- Test integrity: a README under `tests/` is no longer treated as a test or an acceptance test.
- Docs: skills mode (Copilot default) invokes commands as `/speckit-plan` rather than `/speckit.plan`; scripted set-ups
  pass `--non-interactive` to `specify init`.

## 1.0.1 — 2026-10-08
- Traceability: requirement prefixes are configurable (`[traceability] id_prefixes`, e.g. `BR` and `DR` from a PRD), so
  business rules and data requirements can be traced to tests like FR-### items.
- Agent guard: project-specific secret paths (`[agent_policy] secret_paths`) are never readable by agents.
- Test integrity: removing or changing any bold requirement ID line (`**XX-nn**`) in spec.md counts as a protected change.
- Spec Kit preset: `speckit_version >= 0.16.1`, so it can be tried with the WBD golden template (validate first).
- Readiness doctor: Spec Kit counts as initialised only when `.specify/templates` or `.specify/scripts` exist, and a
  constitution whose **Ratified** line says pending/TBD is reported as a draft rather than ratified.
- Agent guard: the dependency message no longer cites a constitution article number (projects renumber articles).
- Reference pilot (delivered separately as `busby-mam-delivery-pilot.zip`): every SEED file filled in for a real
  TypeScript integration, including a zero-dependency architecture-rules check and a Windows setup script.

## 1.0.0 — 2026-10-08
- First release of the Agentic Delivery Kit: repo template (AGENTS.md, tool pointers, six role agents, six skills, path
  instructions, hooks, CI quality gates, PR template, CODEOWNERS, standards and templates), stdlib Python harness scripts
  (verify, traceability, test integrity, agent guardrail hooks, readiness doctor, feature status), Spec Kit preset
  `agentic-delivery`, Spec Kit workflow `agentic-sdd`, continuous-loop cards, tier-aware installer.
