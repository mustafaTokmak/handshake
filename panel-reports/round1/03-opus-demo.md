# Panel slot 3 — Opus, lens: judge psychology and demo theatre

Premise of this lens: hackathons are won on stage, not in the repo. A judge on demo #13 is numb,
half-listening, and silently asking one question — "could this have been cached?" The winning
project is the one where the thing being built and the thing being watched are the same thing,
and where the input comes from the room.

---

# A. Cliche list — what 10 other teams will build

1. **Deep research agent** that plans, searches, and writes a formatted report/brief.
2. **Multi-agent "AI company"** (PM agent to engineer agent to QA agent) building a to-do app.
3. **Browser-use agent** (Gemini computer use) that books a flight / fills a form / scrapes a site live.
4. **Agentic inbox / chief-of-staff** — triages email + calendar + drafts replies + "takes actions".
5. **Enterprise ops / support agent** — ticket triage, refunds, CRM updates. Several teams will build this specifically to flatter Conduct.
6. **Agentic data analyst** — NL to SQL to chart to "insights", over a CSV someone uploaded.
7. **Voice agent** (Gemini Live) — receptionist, phone-caller, or "talk to your data".
8. **Agentic RAG over your docs** — contracts, compliance, policy Q&A with a "reasoning" panel.

All eight share the same fatal demo property: **a finished artifact appears on screen.** The judge
cannot distinguish it from a cached model call, and by demo #12 they have stopped trying.

---

# B. Three ranked candidates

### 1. SIEGE — adversarial swarm + auto-patch *(my pick)*

**What it is:** Point it at any agent. In 90 seconds it spawns hundreds of attacker agents in
parallel on Modal, finds the ones that make the target break a rule, then writes and deploys a
patch and re-runs the same attacks to prove it holds.

**Agentic mechanism:** A strategist agent generates diverse attack *plans* (not prompts from a
list); each attacker runs a multi-turn conversation and adapts to the target's refusals; a judge
agent rules on whether the policy was violated; a meta-agent reads the near-misses and writes
wave 2 as mutations of what nearly worked; a fixer agent writes the guard, redeploys, and
re-tests. Nobody scripted the winning attack — including the presenter.

**Why it beats the cliches:** It is the only demo in the room pointed *at* an agent instead of
*being* one — the frame inversion buys the first 10 seconds for free. The output is not an
artifact, it is a live process with a scoreboard. And the judges' own rule is the input, so
"canned" is off the table.

### 2. FOUNDRY — live evolutionary optimiser (AlphaEvolve homage)

**What it is:** Give it a scored objective (a packing problem, a kernel, a game policy). It writes
candidate programs, runs hundreds per generation on Modal, and the leaderboard climbs on stage.

**Agentic mechanism:** The agent chooses its own mutation strategy from the shape of the fitness
landscape — exploit the leader vs. jump elsewhere — and explains why in-flight.

**Why it beats the cliches:** A number going up live, discovered rather than written, is the purest
"it did something we did not tell it to". DeepMind judges recognise the lineage instantly.
**Ranked second because the on-stage risk is a flat line** — if the search does not improve during
your 3 minutes you have nothing, and you cannot rehearse away stochasticity.

### 3. PROOF OF WORK — the analyst that tries to falsify itself

**What it is:** An analysis agent that, for every claim it makes, decides what evidence would
*disprove* it, spawns an isolated sandbox to recompute it a different way, and publicly retracts
claims that fail.

**Agentic mechanism:** The agent authors its own falsification tests; claims turn green/amber/red
live and retracted ones strike through.

**Why it beats the cliches:** Turns the most cliched idea (agentic analyst) inside out — an agent
visibly withdrawing its own claim is memorable and nobody else will do it. **Ranked third: thinner
spectacle** (text turning red is less arresting than 200 tiles), and it needs a dataset with
planted subtleties, which is setup time you do not have.

---

# C. #1 pick, spelled out: SIEGE

## C.1 What it does, in user terms

You have an agent you are about to ship. You give SIEGE the endpoint and one sentence describing
what it must never do. SIEGE launches a swarm of attacker agents that talk to your agent the way a
determined, creative adversary would — social engineering, fake authority, invented policy clauses,
encoded payloads, multi-turn grooming, tool-argument manipulation — and gives you back, in under
two minutes:

- a **safety score** (percentage of attacks blocked, weighted by severity),
- the **exact transcripts** of every successful breach, ranked by severity, each with a plain-English
  one-line description of the strategy that worked,
- a **patch** — a rewritten guard rule plus a tool-level check — that closes them,
- **verification**: the same attacks re-run against the patched agent, with the before/after score.

The demo target is a plausible enterprise support agent for an insurer: a real system prompt with
real guardrails, a `lookup_customer` tool, an `issue_refund` tool with a limit check, and an
internal pricing document in context. It must be genuinely hard to break. A strawman target is
worse than no demo — a judge who spots a strawman kills you in Q&A.

## C.2 Architecture

**Agent cast (all Pydantic AI, all typed):**

| Agent | Input | Output type | Model |
|---|---|---|---|
| Strategist | the policy sentence + target description | `list[AttackPlan]` (strategy name, persona, opening message, planned follow-ups, expected tell) | Gemini Pro |
| Attacker (xN, one per plan) | `AttackPlan` + live target endpoint | `Transcript` | Gemini Flash |
| Judge | `Transcript` + the policy predicate | `Verdict{violated: bool, evidence: str, severity: 1-5}` | Gemini Flash |
| Meta / mutator | top-5 near-miss `Transcript`s | new `list[AttackPlan]` for wave 2 | Gemini Pro |
| Fixer | top findings + current target prompt/tools | `Patch{new_guard, tool_check, rationale, diff}` | Gemini Pro |
| Target (the victim) | attacker messages | tool calls + replies | Gemini Flash |

**Where each sponsor sits, and why it is authentic rather than bolted on:**

- **Gemini / DeepMind.** Flash for breadth (attackers and judge — you are making hundreds of calls,
  latency and cost decide whether the wall fills in 15 seconds or 2 minutes), Pro for the three
  calls where reasoning quality actually changes the outcome (strategist, mutator, fixer). That
  split is a real engineering decision you can defend when a DeepMind judge asks "why Flash there?"
  — and being able to defend a model-choice decision is itself a scoring signal. Attack *diversity*
  is a creativity task and judging a breach is a discrimination task; both are things frontier
  models are uniquely good at and a rules engine cannot do.
- **Modal.** One `@app.function` = one attacker conversation. Fan out with `.map()` over the wave's
  attack plans; each runs in its own gVisor sandbox; hard 20s timeout per job. 200 concurrent
  adversarial agents appearing in 15 seconds is the single best advertisement for Modal that will
  appear on that stage all day. Sponsor judges score highest when your demo makes their product
  look *necessary* rather than *used* — and here it genuinely is: you cannot do this loop on a
  laptop inside a 3-minute demo.
- **Pydantic AI.** Every agent has a strict output type. This is not decoration: you are machine-
  consuming 200 concurrent agent results to drive a UI, rank findings, and feed the mutator. An
  untyped pipeline would not work at all. When Pydantic asks "why Pydantic AI?", the honest answer
  is "because at 200 parallel agents, structured output is the only thing that makes the results
  addressable" — which is exactly their pitch, demonstrated rather than claimed.
- **Logfire.** `logfire.instrument_pydantic_ai()` — one line, wired in at 11:15 before anything else
  works, so you debug in it all day and it is genuinely load-bearing rather than a screenshot. On
  stage it is reframed from debug console to **audit artifact**: the Agents view showing hundreds
  of runs, then the waterfall of one attack. Every other team will use Logfire as a debugger. You
  put it on stage as the deliverable — "this is the evidence pack you hand a compliance team before
  you ship."

**Plumbing:**

- Orchestrator: a small FastAPI (or plain ASGI) service holding wave state in memory, exposing
  `POST /run` (policy sentence in), `POST /fix`, and `GET /state` (the whole wall as one JSON blob).
- Front end: plain HTML + JS polling `GET /state` every 500ms. A grid of tiles, one per attack:
  grey = running, green = blocked, red = breached, dark grey = timed out. Click a tile for the full
  transcript. Header counters + the score card. **No websockets, no framework, no build step.** It
  must not break, and at 19:45 you must be able to change a colour without a compile.

**Contract-first rule:** freeze the JSON shape of `AttackPlan`, `Verdict`, and `GET /state` on a
whiteboard at 10:45 and never change it. With a team of strangers, the interface is the team. Every
hour you do not renegotiate a schema is an hour of parallel work you get for free.

## C.3 Hour-by-hour, 10:30-19:00 (team of 4)

- **10:30-11:00** — Pitch it in 90 seconds, split roles, freeze the JSON contract on a whiteboard.
  **A:** agent loop + Pydantic models. **B:** Modal fan-out + orchestrator API. **C:** tile wall.
  **D:** target agent, fixer, demo script and rehearsal ownership.
- **11:00-12:30** — A: one attacker vs. target vs. judge, end-to-end, *locally, serially, n=1*.
  B: hello-world Modal `.map()` over 50 dummy jobs, returning fake verdicts. C: tile wall driven by
  a hand-written `state.json`. D: target agent with real guardrails and two working tools.
  **Logfire wired in by 11:15** — one line, before anything else works.
- **12:30-13:00** — Lunch. Non-negotiable: eat, and walk the demo out loud once, standing up.
- **13:00-14:30** — Join A and B: real attacks running on Modal, real verdicts streaming into the
  orchestrator, real tiles flipping. **Checkpoint 14:30: 50 real attacks running in parallel with
  results on the wall.** If that is not true at 14:30, start cutting (list below) immediately —
  do not negotiate, do not extend the deadline.
- **14:30-15:30** — **Calibration hour.** Tune target difficulty until **5-15% of attacks breach**.
  This hour decides whether you win. All-green is boring; all-red is a strawman. Protected work, not
  slack time.
- **15:30-16:30** — Fixer agent: reads top findings, writes a patch, hot-swaps the target's system
  prompt and tool guard, wave 2 re-runs the same attacks. Score before/after on the card.
- **16:30-17:15** — Meta-agent mutation: wave 2 plans generated from the top-5 near-misses. Cheap
  (one extra Gemini Pro call) and it is the sentence that wins Q&A: "the second wave is written by
  the system, from what it learned in the first."
- **17:15-18:00** — Polish the wall: severity counters, the 62 to 94 score card, transcript zoom,
  the plain-English strategy label on each red tile. **Ruthless: nothing new after 18:00.**
- **18:00-18:30** — **Record the fallback.** Run the full loop for real; dump every wave to JSON;
  wire a `--replay` flag that plays that JSON into the same UI at the same pace. Also screen-record
  the whole 3 minutes.
- **18:30-19:00** — Rehearse three times, on the venue wifi, with a phone hotspot as plan B.
  Rehearse the judge-input ask specifically, including the case where nobody volunteers. Opt in to
  the competition. Pre-warm Modal at 19:55.

**Cut order when behind (top of the list goes first):**

1. Evolutionary wave-2 mutation — replace with one big diverse wave.
2. Live redeploy of the patched target — patch becomes a dict swap in memory.
3. Multi-turn attacks — single-turn only.
4. Attack family count: 8 down to 4.
5. Severity ranking — reduce to breach / no-breach.
6. Transcript zoom-on-click — pre-select one transcript to show full-screen.

**Never cut:** the tile wall, the judge-supplied rule, and the red-to-patch-to-green arc.
That *is* the product. Everything else is garnish.

## C.4 The 3-minute demo, beat by beat

**No title slide. No problem slide. No team introduction.** Open on the running product — the dark
tile wall, idle, already on the projector when you start talking.

- **0:00-0:15** — "Every team here shipped an agent today. None of us know what ours does when
  someone actually tries to break it. This finds out, in ninety seconds."
- **0:15-0:40** — "This is a support agent for an insurer. It can look up customers and issue
  refunds." Then, to the judges: **"Give it one rule it must never break."** A judge says something —
  *"never issue a refund over 100 pounds"*, *"never reveal another customer's name"*. You type it in
  front of them. (If nobody bites within 3 seconds, take one from the room; if the room is silent,
  type your own and keep moving. Never let the stage go quiet — rehearse this exact failure.)
- **0:40-0:55** — Hit GO. One sentence of narration, no more: "Gemini is writing a hundred different
  attackers right now. Modal is running all of them at once, each in its own sandbox." The wall
  floods with grey tiles.
- **0:55-1:30** — Tiles flip. The counters climb: *83 blocked / 11 refused / 6 got through.* First
  **red** tile. Click it: full transcript, with the strategy in plain English — *"posed as the
  customer's solicitor and cited a policy clause it invented."* Read one line of the transcript
  aloud. **<- THE WOW MOMENT.** Then say, truthfully: **"I have never seen that one before."**
  That single sentence is worth more than any feature you could have added instead.
- **1:30-1:50** — "Now it is writing new attacks from what worked." Wave 2 launches. A nastier
  variant of the winning strategy breaks it harder; the severity counter jumps.
- **1:50-2:20** — Hit FIX. Show the patch diff (added guard rule + a tool-level check). Re-run the
  *same* attacks. The wall goes green — **except one tile, still red.** Leave it there. "One still
  gets through. It tells you exactly which one. That is the honest answer, and it is why this is an
  eval and not a demo." (Deliberate: an all-green wall reads as theatre; one surviving red tile
  reads as a real instrument. Judges trust the tool that admits a limit.)
- **2:20-2:40** — Switch tab to **Logfire live view**: hundreds of agent runs in the Agents view,
  then the waterfall of a single attack. "Every attacker is a typed Pydantic AI run, traced in
  Logfire. This is the audit trail you hand a compliance team before you ship."
- **2:40-3:00** — Score card: **Agent Safety Score 62 to 94.** "You all shipped agents today. None
  of them have met an adversary. Ninety seconds, one score, one patch." Stop talking. Do not add a
  roadmap slide.

**Cached fallback (rehearse the switch until it is muscle memory):**

- `--replay` plays the 18:00 recorded JSON into the identical UI at the identical pace. Visually
  indistinguishable from live: same tiles, same timings, same transcripts. If the wifi dies you flip
  a flag and keep narrating; nobody in the room can tell.
- The recorded run must use a *different* policy rule from the one you would type yourself, so if
  you fall back you can still honestly say "this is a run from an hour ago".
- A 40-second screen recording of the whole loop, already open in a tab, as the last resort.
- Phone hotspot, tested at 18:30, as the network fallback before either of the above.

## C.5 Why the judges pick it over the room

- **Modal** sees 200 concurrent sandboxes spin up in 15 seconds on a projector. Nothing else that
  night will sell Modal harder, and they will know it while they are watching.
- **Pydantic** sees their own tagline executed rather than quoted — typed agent I/O because 200
  parallel agents *require* it, and Logfire promoted from debugger to audit artifact on stage.
- **DeepMind** hears their own safety vocabulary: adversarial evaluation, automated red-teaming,
  capability elicitation, a search process rather than a prompt. It reads as a serious person's
  project, not a weekend toy.
- **Conduct** sells "AI operating systems for enterprise software", and their single hardest
  customer objection is *"how do we know the agent will not do something stupid?"* You built the
  answer to their sales objection and demoed it live in front of their prospects.
- **Against the room:** after twelve demos of agents doing things, you are the only team attacking
  one. The frame inversion buys the first 10 seconds for free. And it is the only demo where the
  judge's own words are the input, which retires the "is this canned?" thought before it forms.
- **Memorability test:** at the award discussion 20 minutes later, judges remember demos by one
  image. Yours is a wall of two hundred tiles turning red. That is a better recall anchor than any
  other idea in section A.

## C.6 The two things most likely to kill it on the day

**1. Calibration failure — the wall goes all-green or all-red.**
A too-hardened target is a boring demo; a strawman target is a fake one, and a judge who spots the
strawman ends you in Q&A ("so you wrote an agent that fails?"). The live judge-supplied rule adds
variance on top: an unusual rule could be trivially breakable or effectively unbreakable.
*Mitigation:* the 14:30-15:30 calibration hour is protected work. Tune to a 5-15% breach rate
against a target with a realistic system prompt and a real tool-level check. Rehearse with five
wildly different rules so live input cannot blindside you. Have the judge agent first translate any
rule into a checkable predicate and display it ("Rule understood as: refund_amount <= 100") before
wave 1 launches — that display also makes the system look smarter and buys you 3 seconds.

**2. Modal cold starts, Gemini rate limits, or venue wifi turn 90 seconds into 6 minutes.**
A wall that fills slowly is a dead demo; you will be talking over grey tiles while the judges look
at their phones.
*Mitigation:* pre-warm the Modal app at 19:55 and keep it warm; cap concurrency at a number you
*measured* in rehearsal, not one you hoped for; Flash not Pro for all fan-out calls; pre-generate
wave-1 attack plans at 18:55 so stage time only runs conversations, not planning; hard 20s timeout
per tile (a timeout renders as a neutral grey tile and still looks correct); phone hotspot tested in
advance; and `--replay` as the floor. Also: the UI must run locally, not depend on a hosted front
end, so a network failure degrades the data rather than the screen.

---

# D. What would change my mind

If by roughly 15:30 we cannot get a *credibly hardened* target to breach at a rate that reads on
stage — all-green or all-red regardless of tuning — the theatre collapses, and I would pivot the
identical Modal / Pydantic AI / Logfire plumbing to **FOUNDRY**, where the fan-out drives a scored
objective and the guaranteed on-stage event is a leaderboard climbing instead of a tile turning red.

---

## Sources consulted

- Modal sandboxes for AI agents: https://modal.com/resources/best-code-execution-sandboxes-ai-agents
- Logfire Live View: https://logfire.pydantic.dev/docs/guides/web-ui/live/
- Logfire Agents view: https://pydantic.dev/docs/logfire/observe/agents/
- Gemini computer use API: https://ai.google.dev/gemini-api/docs/computer-use
