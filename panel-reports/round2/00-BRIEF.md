# ROUND 2: RED-TEAM THIS RECOMMENDATION

A 10-model panel just recommended a hackathon project. Your job is NOT to be agreeable. Attack it, or tell me honestly it survives.

## The event
{Tech: Europe} Agentic AI Hack, London, one Saturday. Co-hosts Google DeepMind ("Frontier AI Models") and Conduct ("AI operating systems for enterprise software"). Tech partners Modal ("high-performance AI infrastructure") and Pydantic ("Build agents you'll actually ship to production" - Pydantic AI + Logfire). Free credits from all partners. 70 participants cap.
Schedule: 09:30 doors, 10:00 opening + MATCHMAKING (teams form on the day, possibly with strangers), 12:30 lunch, 19:00 competition opt-in deadline, 20:00 live demos (~10-18 teams, ~3 min each), 20:45 awards.
Real build time: ~8.5 hours (10:30-19:00), venue wifi, live on stage in front of the sponsors.

## The recommendation under attack: "UNWIND - rollback for agents"

**Concept.** Your ops agent ran overnight, misread "Acme Ltd" as "Acme Corp", and offboarded the wrong customer: 12 CRM fields changed, 2 contacts deleted, a GBP 4,200 refund issued, a termination email sent, a config file committed to a repo. You hit UNDO. Unwind reads the agent's execution trace, reconstructs what changed, and shows a plan: what it reverses automatically, what it CANNOT reverse and what it proposes instead, and where a human has since touched the same data so it refuses to clobber them. It dry-runs the inverse plan against a forked copy of the world, reports the residual delta, then executes.
Stage line: "Every team tonight gave an agent write access to something. We built the thing that makes that safe."

**Architecture.** A fake world `enterprise-sim` (FastAPI + in-memory state + JSON snapshot) deployed on Modal, ~120 lines, six typed tools (CRM, Billing, Files, Messaging, Email [deliberately irreversible], Calendar), every signature a Pydantic model, plus one real GitHub commit/revert tool, and a `/reset` endpoint from hour one. An actor agent ("Ops Copilot", Pydantic AI + Gemini Flash) makes a realistic mess fast. Every tool call writes a typed `Effect` record (tool, validated args, before/after snapshot, causal parent) to our own ledger - Logfire is the receipts, not the critical path. The Unwind agent (Pydantic AI + Gemini Pro) runs five stages: ledger reader -> classifier (reversible/compensable/irreversible) -> inverse synthesiser (validated against the SAME Pydantic tool registry, so a structurally invalid undo cannot be emitted) -> planner (dependency-ordered reverse, conflict detection vs current state) -> executor with a human gate on irreversible/conflicted rows. Modal forks the world into a sandbox and replays the whole inverse plan there first, diffing against the pre-incident snapshot to report residual delta. UI is one page, three panes, plain HTML+JS polling every 500ms.

**Demo (3 min).** 0:00-0:20 frame. 0:20-0:55 run the actor live, 14 tool calls stream down, board turns red, presenter says nothing. 0:55-1:05 "Undo." 1:05-1:45 THE WOW: plan renders as a typed table, 9 rows auto-reversible, ONE row CONFLICT ("a human edited this 40 seconds ago; we will not clobber their change"), ONE row IRREVERSIBLE ("email delivered, cannot unsend; retraction drafted, routed to a named human"). 1:45-2:10 Modal dry-run shows residual delta 0 of 12, execute for real, board goes green, repo shows a revert commit. 2:10-2:35 Logfire tab; punchline "the undo is itself an agent run, so the undo is undoable." 2:35-3:00 close.
Anti-canned move: before hitting Undo, ask a JUDGE to edit one field in the live world - their edit becomes the CONFLICT row.
Fallback layers: cached trace fixture (hard rule: if the live mess has not landed in 25s, switch mid-sentence); 90-second screen recording; one slide screenshot of the plan table.

**Build plan.** 10:30-11:00 scope lock, three lanes (World+Tools / Undo Brain / UI+Demo), one person owns UI exclusively, freeze JSON shapes on a whiteboard. 11:00-12:00 world sim + tool registry + ledger, DEPLOY TO MODAL BEFORE NOON. 12:00-13:00 actor makes a repeatable mess, `/reset` works, capture canonical trace fixture BY 13:00. 13:00-14:30 classifier + inverse synthesiser + planner (two people). 14:30-15:30 UI wired to live state. 15:30-16:30 Modal sandbox dry-run + residual delta. 16:30-17:15 the two credibility beats (irreversible email, conflict detection). 17:15-18:00 real GitHub revert. 18:00-18:30 record fallback, FREEZE CODE. 18:30-19:00 rehearse 3x on venue wifi, opt in.
Cut order: GitHub -> Modal dry-run (degrade to local preview) -> conflict detection -> 6 tools down to 4. Never cut: the irreversible-email beat, `/reset`, the recorded fallback.

**Stated rationale for picking it.** (a) ~1/3 to 1/2 of live hackathon demos visibly fail; winners come almost entirely from the set whose demo works end-to-end; ambition correlates negatively with winning at 8.5h scope. (b) The rejected alternative, "SIEGE" (200 attacker agents swarm a target agent in parallel Modal sandboxes, find breaches, auto-patch, re-verify, score 62->94), has a central risk OUTSIDE the team's control: it needs a 5-15% breach rate against a credibly hardened target, all-green is boring and all-red is a strawman a judge kills in Q&A, and you only learn which you have around 15:00 with no time to pivot. (c) Nobody else will build rollback; agent red-teaming is a well-known 2026 hackathon shape. (d) It hits Conduct's hardest sales objection and Pydantic's exact tagline.

**Also established in round 1:** the idea is maybe 20% of P(win); the binding constraints are who you team with at 09:35, whether the demo still runs at 20:02, and how much was pre-built before Saturday. Baseline P(first) about 7%, rising to 12-18% with a clean rehearsed sponsor-stack demo. Partner prizes are softer competition than the grand prize.

## What I want from you
Be adversarial and specific. Vague concerns are worthless.
1. **The strongest argument this pick is WRONG.** Not a caveat - the actual case against.
2. **The single most likely failure**, concretely, naming the hour it happens and what precisely breaks.
3. **Is the 3-minute demo legible to a tired judge at demo #12?** Unwind requires the audience to hold a counterfactual in their head (what the world was before) to appreciate the undo. SIEGE just shows tiles turning red. Does the wow moment actually land, or does it need explanation the presenter has no time for?
4. **Was SIEGE wrongly rejected?** Re-argue it if you think so.
5. **What is the single highest-leverage change** to the plan as written?
6. **Your verdict:** BUILD UNWIND / BUILD SIEGE / BUILD SOMETHING ELSE (name it in one line). Commit to one.

Keep it tight. No preamble, no restating my brief back to me.
