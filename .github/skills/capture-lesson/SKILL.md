---
name: capture-lesson
description: "Turn a human correction into a reusable candidate rule with an example, and propose making it an automated check. Use whenever the human corrects your approach, output or assumptions, or when the same mistake happens twice."
---
<!-- Agentic Delivery Standard v1.0 · tier: STANDARD (kit-managed; generated identically for Copilot and Claude Code) -->

# Capture a lesson

1. **Name the pattern**, not the incident: "When X, do Y — because Z".
2. **Show the example**: before (what was done) → after (what should be done), with file paths if useful.
3. **Bound it**: where it applies, and where it must not.
4. **Add a candidate** to `docs/agent-memory/lessons.md` under *Candidates* (newest first) using the template there.
   Do **not** edit AGENTS.md, skills or instruction files yourself — they are protected; a human promotes the rule.
5. **Propose a sensor** if the rule can be checked mechanically (lint rule, architecture rule, test, hook pattern) — add a row
   to `docs/agent-memory/harness-backlog.md`. A check beats a sentence.
6. **Mention it** under *New rule* in your output contract.

A rule from one incident with no example is noise. The same mistake twice means the existing lesson is unclear — propose a rewrite.
