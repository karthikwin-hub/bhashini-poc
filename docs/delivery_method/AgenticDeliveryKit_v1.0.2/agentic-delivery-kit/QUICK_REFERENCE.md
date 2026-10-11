# Agentic Delivery — Quick Reference (one page)

**Humans steer · agents execute · sensors decide · humans accept.**   Spec it → Harness it → Loop it → Graph it → Steer it.

## 1. Pick the lane
| Lane | When | Process (Spec Kit skill names in brackets) | Human gates |
|---|---|---|---|
| 0 Chore | Typos, config, dependency bumps, docs | Issue → agent → PR with `verify.py` evidence | PR review |
| 1 Bug | Something behaves wrongly | `specify extension add bug` → [speckit-bug-assess] → [speckit-bug-fix] → [speckit-bug-test]; failing reproduction test first | Assess result · PR |
| 2 Small change | One module, ≤ ~2 days, low risk | [speckit-specify] → [speckit-plan] → [speckit-tasks] → [speckit-implement] → [speckit-converge] | G1 light · G4 |
| 3 Feature | Cross-module, new data, integrations, security-relevant | Full flow below (or `specify workflow run agentic-sdd`) | G1 · G2 · G3 · G4 |
| 4 Idea | Value or feasibility unclear | `specify extension add assess` → intake → research → define → shape → decide | Go / clarify / kill |
| Spike | Need to learn fast | Vibe-code on a throwaway branch; capture the learning in a spec; **never merge the spike** | — |

## 2. Lane 3 flow
`/speckit.constitution` (once) → **specify → clarify → [G1 Spec Ready] → plan → checklist → [G2 Design Ready] → tasks → analyze
→ acceptance tests (test-designer) → [G3 Ready to Build] → implement ⇄ verify → converge (repeat until Converged)
→ independent review → checks.md → [G4 Done] → PR → human merge → pipeline release**

Skills mode (Copilot default, WBD golden template): type `/speckit-plan` instead of `/speckit.plan` - same commands.

| Gate | Pass when | Owner |
|---|---|---|
| G1 Spec Ready | No [NEEDS CLARIFICATION]; FRs testable; Given/When/Then incl. negative cases; NFRs measurable; scope explicit | Spec owner (BA/PO) |
| G2 Design Ready | Constitution check; owning modules reused; contracts + data model; harness & verification plan; rollback | Tech lead |
| G3 Ready to Build | Analyze: no CRITICAL/HIGH; every FR/AS → task + test; P1 acceptance tests reviewed | Spec owner + tech lead |
| G4 Done | verify PASS · traceability complete · Converged · review clean · checks.md evidenced | Tech lead (+ spec owner accepts) |

## 3. The inner loop (every task)
Restate → survey → smallest change → `python scripts/harness/verify.py --fast` → fix the cause → tick task → commit → update progress.md
**Stop rules**: same failure twice → stop and re-plan · scope grows → stop and ask · unknown tool/key → report, never invent.

## 4. "Done" = it ran · it's scoped · it's reversible · it's readable
Before done: `python scripts/harness/verify.py` (full). Never weaken, skip or delete tests or acceptance criteria to get green.

## 5. Output contract (end of every agent task / PR)
0 Needs from you · 1 What changed · 2 Evidence · 3 Skipped · 4 Blocked · 5 Rollback · 6 New rule

## 6. Gates — always a human
Send outward · merge/release/deploy/publish · delete data / rewrite history / force-push · secrets, access, permissions ·
new dependency or service · change acceptance criteria, acceptance tests, constitution, AGENTS.md, CI, hooks · spend money · expand scope.

## 7. Designing any loop
Trigger · Goal (done = an exit code, not an opinion) · Verifier (not the generator) · Stop rules · Budget (iterations + tokens/cost)
· State outside the model · Escalation path · Least privilege. Start report-only.

## 8. Useful commands
| Purpose | Command |
|---|---|
| Inner-loop checks / full checks | `python scripts/harness/verify.py --fast` / `python scripts/harness/verify.py` |
| Requirements → tests | `python scripts/harness/check_traceability.py [--strict] [--write]` |
| Tests not weakened | `python scripts/harness/check_test_integrity.py --base origin/main` |
| Where is this feature? | `python scripts/harness/sdd_status.py` |
| Is this repo agent-ready? | `python scripts/harness/harness_doctor.py` |
| Run the delivery graph | `specify workflow run <kit>/spec-kit/workflows/agentic-sdd/workflow.yml -i spec="…"` |

## 9. Corrections compound
Corrected? → candidate in `docs/agent-memory/lessons.md` (When X, do Y + example) → weekly review → promote to a rule, or better,
a check → prune rules that stopped firing.
