# CLAUDE.md

<!-- Agentic Delivery Standard v1.0 · tier: SEED. Claude Code reads CLAUDE.md first. When a CLAUDE.md exists, Claude Code does
     NOT also read AGENTS.md by default, so we import it explicitly (works on every Claude Code version and cloud provider). -->

@AGENTS.md

## Claude Code specifics
- Use plan mode for Lane 2+ work until the plan (or the Spec Kit plan.md) is approved.
- Subagents: `.claude/agents/` · Skills: `.claude/skills/` · Hooks and permissions: `.claude/settings.json` (human-owned — do not edit).
- Bounded loops: give `/goal` a deterministic finish line and a limit, e.g.
  `/goal python scripts/harness/verify.py exits 0 — stop after 5 attempts`.
- Personal, uncommitted preferences go in `CLAUDE.local.md` (git-ignored) — never put team rules there.
