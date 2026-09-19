# Panel slot 04 — Opus, contrarian / anti-cliche lens

Event: {Tech: Europe} Agentic AI Hack, London. Co-hosts Google DeepMind + Conduct. Tech partners Modal + Pydantic. 70 people, teams formed on the day, ~8.5h build, live 3-min demo at 20:00.

---

## A. Cliche list — what 10+ of the other ~15 teams will build

Calibrated off the actual project galleries from the recent London/SF Gemini and agent hackathons (46 projects in the Gemini 3 London gallery, 62 in SF, plus the Zero-to-Agent Vercel x DeepMind London gallery and the MongoDB.local London agentic hackathon), adjusted for the fact that this particular room is Pydantic AI + Modal + "AI operating systems for enterprise software".

1. **"Deep research" multi-agent swarm** — planner to N parallel searchers to synthesiser, streaming into a report UI. Two or three teams. At least one will describe it on stage as "a team of 5 specialised agents with shared memory".
2. **Agentic inbox / calendar chief-of-staff** — triages email, books meetings, drafts replies, protects focus time. Guaranteed; usually pitched by a founder-type who has felt the pain personally.
3. **A coding agent with a twist** — "Cursor for X", autonomous PR fixer, test writer, legacy migration agent, dependency upgrader. The London Gemini gallery alone had four of these (DAndy, Effectiv, Ordan, petar-and-ivelin). Expect 2-3 here, at least one of them "agent that writes the tests for the PR".
4. **Enterprise support-ticket / ops triage agent** — reads a ticket, queries internal systems, drafts a resolution, escalates when unsure. The Conduct sponsorship actively baits this one. Expect 3+, and expect them to look nearly identical to each other.
5. **Browser-use / computer-use agent doing a tedious form flow** — booking, procurement, expense filing, government forms. Flashy, and breaks on stage roughly half the time. One or two teams.
6. **Voice agent that books / orders / negotiates something** — Gemini Live, a phone on the table, someone calling a restaurant. Reliable crowd-pleaser, weak on agency.
7. **Agent observability / eval dashboard** — someone will notice Logfire is in the room and build "Datadog for agents" or "an LLM-judge harness for agent trajectories". One team, possibly two, and they will ship a dashboard with no actual agent in it.
8. **Vertical RAG copilot with citations** — legal, medical, planning permission, compliance, procurement docs. Cf. PlanPass AI winning MongoDB London. Always present; rarely wins an explicitly *agentic* hack because retrieval is not autonomy and judges know it.
9. **MCP server / A2A protocol plumbing demo** — "we turned every tool in your company into an MCP server and let agents discover each other". Impressive to two judges, illegible to the rest of the room in three minutes.

The structural weakness shared by every single one of them: **they all demo an agent *starting* work.** Not one of them demos what happens when the agent is wrong. That gap is the whole opportunity.

---

## B. Three ranked contrarian candidates

**1. Unwind — rollback for agents.**
*What it is:* an agent that reads another agent's execution trace and undoes what it did, across systems that share no transaction.
*Agentic mechanism:* it reasons about **semantic compensation**. For each recorded effect it decides reversible / compensable / irreversible, synthesises a typed inverse action, orders the inverse plan by dependency (reverse-topological, not just reverse-chronological), detects state that has changed since the incident so it never clobbers a human's later edit, dry-runs the entire plan against a forked world, and escalates what genuinely cannot be undone with a drafted remedy.
*Why it beats the cliches:* it is the only demo in the room that inverts the framing — its output is *less* work existing in the world — and it is the precondition for every other project pitched that evening. Nobody grants an agent write access to Salesforce, Stripe or prod without an undo button, and every judge in the room already knows that.

**2. Necromancer — the deletion agent.**
*What it is:* point it at a repo plus the cron / Zapier / Lambda / scheduled-job sprawl around it, and it finds the automations nobody owns, proves they are dead, and files deletion PRs.
*Agentic mechanism:* it designs its own evidence-gathering experiments per suspect — instrument and observe, shadow-run, canary-disable, check downstream consumers — rather than doing static analysis. It has to decide what evidence would be sufficient, which is genuine autonomy.
*Why it beats the cliches:* it is the anti-coding-agent. Everyone else generates; this removes. Ranked second only because on a projector it risks *reading* as "a coding agent", which is cliche #3, and the pitch has ten seconds to escape that gravity.

**3. No. — the agent for people who hate agents.**
*What it is:* an agent with exactly one power: declining. It cancels subscriptions, kills recurring meetings that produce no decision, unsubscribes, refuses calendar invites, and sends the awkward no on your behalf.
*Agentic mechanism:* it has to decide what is safe to refuse, gather the evidence that a thing is dead weight (meeting has produced no artefact in 8 weeks; subscription unused for 90 days), and execute cancellation flows end to end.
*Why it beats the cliches:* perfectly orthogonal to the "agent as eager intern" framing everyone else uses, and genuinely funny on stage. Ranked third because it is too small to win an infrastructure-sponsored hackathon — it is a great consumer app at the wrong event.

---

## C. The pick, spelled out: **Unwind**

### C1. What it does, in user terms

Your ops agent ran overnight. It misread "Acme Ltd" as "Acme Corp" and offboarded the wrong customer: 12 CRM fields changed, 2 contacts deleted, a GBP 4,200 refund issued, a termination email sent, a config file committed to a repo.

You open Unwind and hit **Undo**.

Unwind reads the agent's execution trace, reconstructs exactly what changed in the world, and shows you a plan: what it will reverse automatically, what it *cannot* reverse and what it proposes to do instead, and where a human has touched the same data since and it refuses to overwrite them. It dry-runs the whole plan against a clone of your systems and reports the residual delta. Then it executes. Green board in forty seconds.

The one-line version for the stage: **every other team tonight gave an agent write access to something. We built the thing that makes that safe.**

### C2. Architecture

**The world — `enterprise-sim`.** A FastAPI app deployed on **Modal**, in-memory state plus JSON snapshot, roughly 120 lines. Six typed tools: CRM (accounts, contacts), Billing (refunds), Files (documents), Messaging (post / delete), Email (send — deliberately irreversible), Calendar. Every tool signature is a **Pydantic** model in and out; the registry is the single source of truth for both agents. Plus exactly one *real* tool: GitHub commit / revert. A `/reset` endpoint exists from hour one — it is what makes rehearsal possible.

**The actor agent — "Ops Copilot".** **Pydantic AI** + **Gemini 3 Flash** (chosen for speed: the mess must land in under 25 seconds on stage). Instrumented with **Logfire**. Its only job is to make a realistic mess fast, given a subtly wrong ticket.

**The effect ledger.** Every tool call writes a typed `Effect` record: tool name, validated args, before/after snapshot where obtainable, causal parent. Logfire spans are the *receipts* shown on stage; our own typed ledger is the *load-bearing* store. Critical design decision: do not make the demo depend on reading Logfire's API live over venue wifi. Logfire is the credibility tab, not the critical path.

**The Unwind agent.** Pydantic AI, **Gemini 3 Pro** — this is the reasoning-heavy part, the bit DeepMind judges actually care about. Five stages:
- *Ledger reader* — pulls the trace, materialises typed `Effect` objects.
- *Classifier* — Gemini labels each effect `reversible` / `compensable` / `irreversible` with a justification.
- *Inverse synthesiser* — emits a proposed inverse action **validated against the same Pydantic tool registry**, so a structurally invalid inverse literally cannot be emitted. This is the single strongest Pydantic story in the project and it should be said out loud.
- *Planner* — dependency-aware reverse ordering, plus conflict detection against current world state (has anything changed since?).
- *Executor* — runs the plan, with a mandatory human gate on every `irreversible` or `conflict` row.

**Modal, doing what Modal is for.** Fork the world into a sandbox, replay the entire inverse plan there first, diff the resulting state against the pre-incident snapshot, and report the residual delta ("0 of 12 fields outstanding"). This is the beat that makes the project read as infrastructure rather than a script. It is also the honest engineering answer to "how do you know your undo is correct?".

**UI.** One page, three panes: World State (diff-highlighted), Effect Timeline (colour-coded by classification), Undo Plan (the table with the CONFLICT and IRREVERSIBLE rows). Logfire open in a second browser tab as the receipts.

Sponsor fit, stated plainly: Gemini does the hard semantic reasoning; Modal runs the world and the verification sandbox; Pydantic AI structures both agents and Pydantic models make the inverse actions provably well-formed; Logfire is the trace that the whole product consumes. Nothing is bolted on — remove any one of the four and the project stops working.

### C3. Hour-by-hour, 10:30-19:00

- **10:30-11:00** — Team formation and scope lock. Three lanes: World+Tools, Undo Brain, UI+Demo. **One person owns the UI from minute zero and touches nothing else** — this is the most commonly skipped and most commonly fatal decision at a one-day hack.
- **11:00-12:00** — World sim, typed tool registry, effect ledger. **Deploy to Modal before noon**, not at 18:00. A thing that has never been deployed is not a thing.
- **12:00-13:00** — Actor agent produces a repeatable mess. Snapshot / restore / `/reset` working end to end. Capture one canonical trace to disk as a fixture — this is the fallback, and it must exist by 13:00, not by 18:00.
- **13:00-14:30** — Classifier + inverse synthesiser + planner. The core. Two people on this.
- **14:30-15:30** — UI v1 wired to live state: three panes, diff highlighting, the Undo button.
- **15:30-16:30** — Modal sandbox dry-run and residual-delta report.
- **16:30-17:15** — The two credibility beats, in this order of priority: (a) irreversible email leads to drafted retraction + human escalation row; (b) conflict detection where a human edited a record after the agent did.
- **17:15-18:00** — Real GitHub commit / revert integration.
- **18:00-18:30** — Record the full run as a screen capture. **Freeze code.** No commits after 18:30 except to fix something the rehearsal breaks.
- **18:30-19:00** — Rehearse three times with `/reset` between runs, on the actual venue wifi, with the actual projector if possible. Opt in before the 19:00 deadline.

**Cut order when behind (cut in this exact sequence):**
1. Real GitHub integration — nice, not necessary.
2. Modal sandbox dry-run — degrade to a locally computed plan preview; keep the *language* of verification even if the fork is faked by a second in-process copy of the world.
3. Conflict detection — painful to lose, because it is half the answer to the main objection; lose it only if the alternative is not finishing.
4. Shrink the world from 6 tools to 4 (keep CRM, Billing, Email, Files).

**Never cut, under any circumstances:** the irreversible-email beat, `/reset`, and the recorded fallback video.

### C4. The 3-minute demo script, beat by beat

- **0:00-0:20 — The frame.** "Every team tonight gave an agent write access to something. Here is what nobody demoed: three in the morning, when it is wrong." Clean board on screen.
- **0:20-0:55 — The mess, live.** Run the actor agent on a plausible ops ticket. Fourteen tool calls stream down the timeline. The board turns red: wrong customer offboarded, two contacts deleted, GBP 4,200 refunded, a termination email sent, a file committed to the repo. Say nothing while it runs; let the room watch it go wrong.
- **0:55-1:05 — One button.** "Undo."
- **1:05-1:45 — THE WOW.** The plan renders as a typed table. Nine rows auto-reversible. **One row flagged CONFLICT** — "a human edited this field 40 seconds ago; we will not clobber their change". **One row flagged IRREVERSIBLE** — "email delivered; cannot unsend. Retraction drafted, routed to a named human for approval." Point at that row and say: *this is the only moment tonight where an agent tells you what it cannot do.* That row is the entire pitch. It is what separates this from a clever script, and it is the thing a DeepMind or Pydantic judge will remember at the award ceremony.
- **1:45-2:10 — Proof.** Dry-run the plan on a Modal fork: "residual delta, 0 of 12 fields". Then execute for real. Board goes green. The repo shows a revert commit.
- **2:10-2:35 — Receipts and the punchline.** Switch to the Logfire tab: every undo step traced, same as any other agent run. Then the punchline: the undo is itself an agent run, so **the undo is undoable**.
- **2:35-3:00 — The close.** "Agents get write access to real systems the day rollback exists. That is the unlock. That is what we built." Aimed squarely at Conduct and Pydantic.

**Fallback, in layers:**
- Layer 1: the actor run is replayed from a **cached trace fixture** with zero live model calls. Hard rule agreed in advance: *if the live actor run has not produced the mess within 25 seconds, the presenter switches to the fixture mid-sentence without commentary.* The undo is the demo; the mess is just setup.
- Layer 2: a 90-second screen recording of the full working run, sitting on the laptop desktop, one click away.
- Layer 3: one slide with a screenshot of the plan table, including the CONFLICT and IRREVERSIBLE rows. If literally everything fails, that one image still lands the idea.
- Phone hotspot paired and tested before 19:00. Everything runs against a Modal URL, so the laptop only needs to reach one host.

### C5. Why the judges pick it over the room

- **Pydantic's entire positioning is "agents you'll actually ship to production".** This is the missing production primitive, and Logfire is load-bearing rather than decorative — the product *consumes* the trace, it does not merely emit one.
- **Conduct sells an AI operating system into enterprises.** The blocker they hit in every single sales conversation is write access. This is an answer to it, demoed rather than asserted.
- **Modal is used for the thing Modal is genuinely good at** — forking a world and replaying a plan in an isolated sandbox — not as a place to host a Streamlit app.
- **DeepMind judges reward reasoning that is hard.** Inverse planning over a partially observable, partially irreversible world is a real reasoning task with a visible right and wrong answer, unlike "summarise these documents nicely".
- **Contrast effect.** After fifteen demos of agents enthusiastically starting work, the sixteenth demo is the only one that addresses the problem every judge in that room already knows is the real one. It also quietly makes the other fifteen look incomplete, without ever criticising them.

### C6. Top 2 things most likely to kill it, and mitigations

**1. Scope — you are building two systems in one day.**
You need the mess before you can undo the mess, so roughly 40% of the build is demo world. Be honest about that up front rather than discovering it at 16:00. Mitigation: the world sim is an in-memory dict with a JSON snapshot. No Postgres, no ORM, no auth, no migrations. Deployed to Modal by noon. Anyone who says "let's just use a real database" is overruled by prior agreement made at 10:45. The mitigating grace: the sim is not throwaway — it *is* the typed tool registry that the undo agent validates its inverse actions against, so the work is structural, not scaffolding.

**2. "This is just a saga pattern / an undo log."**
A systems-literate judge — and there will be one — will say you have reinvented compensating transactions and the LLM adds nothing. This is the strongest attack on the project and it must be answered *before* it is asked. Mitigation: name it yourself on stage, in one sentence. "Yes, this is the saga pattern — except nobody has a shared transaction across Salesforce, Stripe and Gmail; the compensations cannot be pre-registered because the agent invents the action sequence at runtime; and some of them are irreversible and need a judgement call about what 'as close to undone as possible' actually means." The CONFLICT row and the IRREVERSIBLE row exist in the demo script *specifically* to prove that sentence rather than assert it. If you cut both of those rows, the objection lands and you lose.

*(Third-order risk worth one line of engineering: Gemini emits a structurally valid but semantically wrong inverse plan live. Covered by Pydantic validation plus one retry plus the cached fixture.)*

### C7. Attacking my own pick, honestly

- **It requires a mess to undo, so the demo world is a real cost.** Roughly two hours of an eight-and-a-half hour day goes into building something that is not the product. Accepted, and mitigated by making the sim double as the tool registry, but it is the single biggest reason this pick could fail to finish.
- **Everything on screen is fake state.** A skeptic can dismiss the whole thing as a puppet show. This is exactly why the one real GitHub integration matters more than its size suggests: one genuinely real side effect, reverted live, makes the fake ones read as real. It is also why it is first on the cut list, which is an uncomfortable tension you should be aware of — cutting it is the safe call, and it is also the call that weakens the demo most per line of code saved.
- **Undo is emotionally negative.** There is a real risk that judges find it unsexy next to something colourful and generative. Mitigation is framing: *the seatbelt is what lets you drive fast.* This is an unlock, not a brake. And the live rogue-agent chaos gives you the flashy half for free — you get the excitement and then the relief, which is a better three-minute emotional arc than steady competence.
- **It is a platform pitch, not a product pitch.** If the panel skews commercial and wants to see a market, "developer infrastructure for a category that barely exists yet" is a harder sell than "here is an app with users". This is a real bet on the composition of the judging panel, and the sponsor list (two infra companies, one frontier lab, one enterprise-OS company) is the reason I think the bet is right.
- **The single point of failure is one row in a table.** If the IRREVERSIBLE row does not render, or the presenter rushes past it, the demo degrades from "these people have thought about this" to "a script that reverses a list". Rehearse that beat specifically. Whoever presents should be able to deliver the 1:05-1:45 window from memory with the screen off.

---

## D. What would change my mind

If the judging rubric or the opening brief turns out to reward a user-facing product with a visible market rather than developer infrastructure, then Unwind is a platform pitch to a consumer-product panel — and I would switch to Necromancer, which carries the same contrarian inversion but lands a countable result on stage ("4,000 lines deleted, 6 dead crons killed, CI green").

---

### Sources used for cliche calibration
- Gemini 3 Hackathon London gallery — https://cerebralvalley.ai/e/gemini-3-hackathon-london/hackathon/gallery
- Gemini 3 Hackathon SF gallery — https://cerebralvalley.ai/e/gemini-3-hack-sf/hackathon/gallery.md
- Zero to Agent: Vercel x DeepMind London — https://cerebralvalley.ai/e/zero-to-agent-london
- MongoDB.local London, Agentic Evolution Hackathon — https://tldrecap.tech/posts/2026/mongodb-local-london/agentic-evolution-hackathon-innovative-solutions/
- Moveworks London AI Agent Hackathon — https://www.moveworks.com/us/en/resources/blog/moveworks-ai-agent-hackathon-london-25
- Devoteam AI Agent Lab London — https://www.devoteam.com/ai-agent-lab-2026-london/
