# {Tech: Europe} Agentic AI Hack — panel verdict

10-model panel, one shared brief, 10 distinct lenses. Raw reports:
`/private/tmp/claude-501/-Users-mustafatokmak-st-claude-projects-agentic-ai-hack/afd6cd31-43c8-44cd-8067-b72d90bdba85/scratchpad/panel/`

| Slot | Model | Lens | Pick |
|---|---|---|---|
| 01 | Codex gpt-5.6-sol | feasibility | **Canary** — red-teams an invoice-approval agent, finds exploit, installs guardrail, re-proves |
| 02 | Codex gpt-5.6-sol | sponsor-tech | **ChangeProof** — rival patches race in parallel Modal sandboxes, verifier invents the counterexample |
| 03 | Claude Opus 5 | demo theatre | **SIEGE** — 200 attacker agents swarm a target agent, breach it, auto-patch, re-verify |
| 04 | Claude Opus 5 | contrarian | **Unwind** — undoes what another agent did; flags what it *cannot* undo |
| 05 | Muse Spark 1.3 | wildcard | **Rogue Intern** — attacker agent robs a fake company, defender agent blocks it, live |
| 06 | DeepSeek v4.1 | agent architecture | **GameSmith** — designs auction mechanisms while exploiter agents attack them |
| 07 | GLM 5.1 | product / startup legs | **Promptly** — autonomous AR collections for B2B SaaS finance |
| 08 | Gemini 3.7 Flash | Gemini capabilities | **RetroAgent** — screen recording of a legacy workflow → self-healing automation |
| 09 | Kimi K3 (Cursor) | base rates | **3AM** — production breaks on stage, agent diagnoses and rolls back the bad deploy |
| 10 | Grok 4.6 (Cursor) | framing | **Airlock** — the agent refuses and rewrites the request under policy |

---

## 1. The cliché list — do not build these

Named independently by 8+ of 10 models. Assume each is pitched 2-3 times:

1. Deep-research agent → planner + parallel searchers + written report
2. Meeting transcript → action items → Jira/Linear tickets
3. Inbox / calendar chief-of-staff that "takes actions"
4. Code-review or auto-PR agent ("Cursor for X")
5. Enterprise support-ticket triage agent — **the Conduct sponsorship actively baits this one, expect 3+**
6. Browser-use agent booking a flight or filling a form (and dying on venue wifi)
7. Voice agent via Gemini Live — receptionist, phone-caller
8. RAG-over-your-docs with a citations panel
9. "Datadog for agents" — someone will notice Logfire is in the room

Opus nailed the shared structural weakness: **all of them demo an agent *starting* work. None demo what happens when it is wrong.** By demo #12 a finished artifact appearing on screen is indistinguishable from a cached ChatGPT call, and the judge has stopped trying to tell.

## 2. The convergence

9 of 10 models, from unrelated lenses, picked the same *family*: **point the agent at a system (or at another agent) and make it do adversarial or corrective work — attack, refuse, verify, or undo — with the failure and its repair visible live.**

Only two fell outside it: Gemini Flash (video → automation) and GLM (AR collections).

That is not ten models agreeing by accident. It is the one shape that satisfies all five constraints at once: it is visibly agentic, it produces motion rather than an artifact, it needs Modal's fan-out for real, it makes Pydantic's typing load-bearing, and it inverts the frame everyone else is using.

## 3. The recommendation: **Unwind**

*Rollback for agents.* Primary pick. **SIEGE is the hedge** — see §6.

### What it is

Your ops agent ran overnight. It misread "Acme Ltd" as "Acme Corp" and offboarded the wrong customer: 12 CRM fields changed, 2 contacts deleted, a £4,200 refund issued, a termination email sent, a config committed to a repo.

You hit **Undo**.

Unwind reads the agent's execution trace, reconstructs what actually changed, and shows a plan: what it reverses automatically, what it *cannot* reverse and what it proposes instead, and where a human has since touched the same data so it refuses to clobber them. It dry-runs the whole plan against a forked copy of the world, reports the residual delta, then executes.

Stage line: **"Every team tonight gave an agent write access to something. We built the thing that makes that safe."**

### Why this over SIEGE

- **Kimi's base rates**: ~⅓ to ½ of live demos visibly fail; winners come almost entirely from the set whose demo works end to end; ambition correlates *negatively* with winning at 8.5-hour scope. Unwind's demo is far more controllable — the mess replays from a fixture, and the undo plan is deterministic given the ledger.
- **SIEGE's central risk sits outside your control.** It needs a 5-15% breach rate against a credibly hardened target. All-green is boring, all-red is a strawman a judge kills in Q&A — and you only learn which you have at ~15:00, with no time left to pivot. Unwind's risk is "did we finish", which you control.
- **Nobody else will build it.** SIEGE is adjacent to cliché #9 and is a well-known 2026 hackathon shape; agent-rollback is not on anyone's list.
- **It indexes off every other demo in the room** — a structural advantage that *grows* with the number of competing teams. It hits Conduct's single hardest sales objection and Pydantic's exact tagline.

### Architecture

- **The world** — `enterprise-sim`: FastAPI + in-memory state + JSON snapshot on **Modal**, ~120 lines. Six typed tools: CRM, Billing, Files, Messaging, Email (deliberately irreversible), Calendar. Every signature is a Pydantic model. Plus one *real* tool: GitHub commit/revert. A `/reset` endpoint from hour one — it is what makes rehearsal possible.
- **The actor** — "Ops Copilot", Pydantic AI + **Gemini Flash** (speed: the mess must land in under 25s on stage). Its only job is to make a realistic mess from a subtly wrong ticket.
- **The effect ledger** — every tool call writes a typed `Effect`: tool, validated args, before/after snapshot, causal parent. *Your own ledger is load-bearing; Logfire is the receipts.* Do not make the demo depend on reading Logfire's API live over venue wifi.
- **The Unwind agent** — Pydantic AI + **Gemini Pro**, five stages: ledger reader → classifier (`reversible` / `compensable` / `irreversible`) → inverse synthesiser → planner (dependency-ordered, conflict-detecting) → executor with a human gate on every irreversible or conflicted row.
- **Modal, doing what Modal is for** — fork the world into a sandbox, replay the whole inverse plan there first, diff against the pre-incident snapshot, report residual delta ("0 of 12 fields outstanding"). This is what makes it read as infrastructure rather than a script, and it is the honest answer to "how do you know your undo is correct?"
- **UI** — one page, three panes: World State (diff-highlighted), Effect Timeline (colour-coded), Undo Plan (the table with the CONFLICT and IRREVERSIBLE rows). Plain HTML + JS polling every 500ms. No framework, no build step.

The strongest Pydantic sentence in the project, say it out loud: **inverse actions are validated against the same tool registry, so a structurally invalid undo literally cannot be emitted.**

### Build plan, 10:30-19:00

| Time | Work |
|---|---|
| 10:30-11:00 | Scope lock. Three lanes: World+Tools / Undo Brain / UI+Demo. **One person owns the UI from minute zero and touches nothing else.** Freeze the `Effect` and `UndoPlan` JSON shapes on a whiteboard — with a team of strangers, the interface is the team. |
| 11:00-12:00 | World sim, typed tool registry, effect ledger. **Deploy to Modal before noon.** A thing that has never been deployed is not a thing. |
| 12:00-13:00 | Actor produces a repeatable mess. `/reset` working. **Capture one canonical trace to disk as a fixture — by 13:00, not 18:00.** That fixture is the fallback. |
| 13:00-14:30 | Classifier + inverse synthesiser + planner. The core. Two people. |
| 14:30-15:30 | UI wired to live state: three panes, diff highlighting, Undo button. |
| 15:30-16:30 | Modal sandbox dry-run + residual-delta report. |
| 16:30-17:15 | The two credibility beats, in priority order: (a) irreversible email → drafted retraction + human escalation; (b) conflict detection where a human edited a record after the agent did. |
| 17:15-18:00 | Real GitHub commit/revert. |
| 18:00-18:30 | Record the full run. **Freeze code.** |
| 18:30-19:00 | Rehearse 3× with `/reset` between runs, on venue wifi, on the actual projector. Opt in before the deadline. |

**Cut in this exact order:** GitHub integration → Modal dry-run (degrade to a local plan preview, keep the *language* of verification) → conflict detection (painful, it is half the answer to the main objection) → shrink 6 tools to 4.

**Never cut:** the irreversible-email beat, `/reset`, the recorded fallback.

### The 3-minute demo

- **0:00-0:20** — "Every team tonight gave an agent write access to something. Here is what nobody demoed: 3am, when it is wrong." Clean board.
- **0:20-0:55** — Run the actor on a plausible ticket. Fourteen tool calls stream down the timeline. Board turns red. **Say nothing while it runs.** Let the room watch it go wrong.
- **0:55-1:05** — "Undo."
- **1:05-1:45 — THE WOW.** The plan renders as a typed table. Nine rows auto-reversible. **One row CONFLICT** — "a human edited this 40 seconds ago; we will not clobber their change." **One row IRREVERSIBLE** — "email delivered, cannot unsend. Retraction drafted, routed to a named human." Point at it: *this is the only moment tonight where an agent tells you what it cannot do.* That row is the entire pitch.
- **1:45-2:10** — Dry-run on a Modal fork: "residual delta, 0 of 12." Execute for real. Board goes green. Repo shows a revert commit.
- **2:10-2:35** — Logfire tab: every undo step traced. Then the punchline: the undo is itself an agent run, **so the undo is undoable.**
- **2:35-3:00** — "Agents get write access to real systems the day rollback exists. That is the unlock."

**Steal this from SIEGE — the anti-canned move.** Before you hit Undo, **ask a judge to edit one field in the world** (the UI has a live state pane; make one field editable). Their edit *is* the CONFLICT row. It costs you nothing, it is the one beat that cannot be faked, and it retires the "is this canned?" thought before it forms. Rehearse the case where nobody volunteers: take one from the room, or do it yourself and keep moving. Never let the stage go quiet.

**Fallback, in layers:** (1) actor run replays from the cached fixture, zero live model calls — hard rule, if the live mess has not landed in 25 seconds the presenter switches mid-sentence without commentary; (2) a 90-second screen recording one click away; (3) one slide with a screenshot of the plan table showing the CONFLICT and IRREVERSIBLE rows — if everything fails, that image still lands the idea. Phone hotspot paired and tested before 19:00.

### What kills it

1. **Scope.** The world sim, ledger, classifier, planner and UI is a lot for strangers. Mitigation: the cut order above, the frozen JSON contract at 10:45, and the 13:00 fixture checkpoint. If the fixture does not exist at 13:00, start cutting immediately — do not negotiate.
2. **Team hijack toward a chatbot.** Grok's point. Mitigation: recruit at 09:35 with a working skeleton already on your laptop. If they insist on a wrapper, join a different team or fork to two people. Do not "merge ideas".

## 4. Grok's reframe — read this before the ideas

Grok rejected the premise, and it is right enough to act on: **the idea is roughly 20% of P(win).** The binding constraints, in order, are who you stand next to at 09:35, whether a demo still runs at 20:02, how much you pre-baked before Saturday, and *then* the idea.

Independent estimate: ~60 of 70 show up, ~15-18 teams form, ~10-14 actually opt in and demo. Baseline P(first) ≈ 7%; a clean sponsor-stack demo with a rehearsed wow gets you to maybe 12-18%. Novelty adds a few points, not a 3×.

**So: arrive with the skeleton built.** The world sim, the typed tool registry, the `/reset` endpoint, the Modal deploy and all four sets of keys working — that is a pre-Saturday job, not a 10:30 job. Greenfield with strangers in 8.5 hours is how you become cliché #1 with a broken demo.

Two more things worth more than the idea:
- **Kimi**: partner prizes are softer competition than the grand prize, because most teams bolt sponsor tech on shallowly. Optimal play is to contend for the grand prize while *locking* a partner prize as the floor. Unwind's floor is the Pydantic prize — Logfire is consumed by the product, not merely emitted.
- **Grok**: if the team is a dumpster fire at 11:00, join a stronger one or skip opt-in and spend the evening on sponsor conversations. EV of looking like the person Conduct/Pydantic/Modal would hire is larger than EV of the prize. Do not die on an idea.

## 5. The shared recipe — true regardless of which idea you pick

Every model that gave a build plan agreed on these:

1. **Own the world.** SQLite/FastAPI on Modal, seeded fixtures. Never a real third-party SaaS API, no OAuth, no ingestion pipeline. Integration work is what eats the day.
2. **Gemini Flash for fan-out, Pro for the 2-3 calls where reasoning quality changes the outcome.** Being able to defend that split when a DeepMind judge asks "why Flash there?" is itself a scoring signal.
3. **Modal's fan-out is the visible motion** and the only thing you genuinely cannot do on a laptop inside 3 minutes. Sponsor judges score highest when the demo makes their product look *necessary*, not *used*.
4. **Pydantic typing must be load-bearing**, not decoration — the honest version is "at N parallel agent results, structured output is the only thing that makes them addressable."
5. **Logfire on a second screen, reframed from debugger to audit artifact.** Everyone else will use it to debug. Put it on stage as the deliverable: "this is the evidence pack you hand a compliance team."
6. **Deterministic `--replay` recorded at 18:00**, playing into the identical UI at the identical pace. Freeze code at 18:30.
7. **Leave one thing visibly broken.** Opus's sharpest note: an all-green wall reads as theatre; one surviving red row reads as a real instrument. Judges trust the tool that admits a limit.

## 6. The hedge: SIEGE

If you land a team of 4 strong engineers and want the higher-variance play, build SIEGE instead: give it a target agent and one sentence it must never violate; it spawns ~200 attacker agents in parallel Modal sandboxes, a judge agent rules on breaches, a meta-agent writes wave 2 from the near-misses, a fixer writes the patch, and the same attacks re-run to prove it holds. Score card: 62 → 94.

Its best assets are the **judge-supplied rule** (kills "is this canned?" outright), a wall of 200 tiles turning red as the single best recall anchor in the room, and the hardest Modal advertisement that will appear all day.

Its cost: the **calibration hour (14:30-15:30 is protected work, not slack)** must land a 5-15% breach rate against a *credibly hardened* target — a strawman target ends you in Q&A. That risk resolves too late to pivot. Full plan in `panel/03-opus-demo.md`.

## 7. Also worth stealing

- **Kimi's 3AM**: let a judge pick which of three rehearsed faults to inject. All three rehearsed = zero risk, large credibility. Same trick as Unwind's judge-edited field.
- **Codex-B** found a real integration worth using: Pydantic AI Harness ships a native `ModalSandbox` giving agents isolated shell/file tools with a fresh sandbox per run. Two sponsors integrated for you, out of the box.
- **Muse's Rogue Intern** is the memorability winner if the room turns out lighter than expected — two agents, one robbing a fake company and one blocking it, is the only demo with conflict and comedy.
- **Grok's framing**: the user-visible object should be *a change ticket with a red refusal*, not a chat transcript. Applies to Unwind directly.

---

### Panel notes

- Codex ran via CLI — the `codex` MCP server failed to connect this session (`CONNECTION_CLOSED`).
- Muse, DeepSeek and GLM ran through opencode; the zen-billed `opencode/*` models are out of credit, so they went via `opencode-go/*`. GLM returned empty on 5.3 and 5.2 and only produced output on 5.1.
- Google Flash ran as `gemini-3.7-flash-high` through Cursor, since `opencode/gemini-3.8-flash` hit the same credit wall.
- Kimi K3 and Grok 4.6 ran through Cursor as requested.
