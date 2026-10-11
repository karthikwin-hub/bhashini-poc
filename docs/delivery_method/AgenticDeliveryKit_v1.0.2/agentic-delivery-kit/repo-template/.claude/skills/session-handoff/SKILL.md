---
name: session-handoff
description: "Start and end agent sessions so work survives context resets: read the handoff state at start, keep progress.md current, and leave one concrete next action. Use at the start of any session on an existing feature, before a long task pauses, and when context is getting full."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Session handoff

## Starting a session
1. Read AGENTS.md, then the active feature: `python scripts/harness/sdd_status.py`.
2. Read `specs/<feature>/progress.md` (create it from `docs/templates/progress-template.md` if missing), then spec.md,
   plan.md and the open tasks in tasks.md. Run `git log --oneline -15`.
3. Inspect the files the handoff mentions before trusting its status.
4. Baseline: `python scripts/harness/verify.py --fast`. A red baseline is the first problem to solve — don't build on it.

## During the session
- One user story per session. Prefer a fresh session with a good handoff over a long, compacted one.
- After each completed task: tick it, commit, update *Completed* and *Next action*.

## Ending (or when context gets heavy)
Update progress.md: Task · Completed (with evidence) · In progress · Decisions (and why) · Open issues and questions for
humans · Failed attempts (don't repeat) · **Next action** (one concrete step). Commit it. A fresh session must be able to
resume from progress.md + git log alone.
