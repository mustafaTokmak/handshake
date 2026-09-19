## A. Cliche list (what 10+ teams will pitch)

1. Meeting agent: joins Zoom, transcribes, creates Jira tickets.
2. Deep-research clone: topic in, sourced PDF report out.
3. Inbox/calendar triage assistant ("it emails people for you").
4. Coding agent: PR reviewer / auto-fix CI / "Devin for X".
5. Travel planner that browser-uses its way to an itinerary.
6. Job-hunt agent: scrapes listings, tailors CV, auto-applies.
7. "Company in a box": CEO/PM/engineer agents chatting in a loop.
8. RAG customer-support copilot over a FAQ knowledge base.

## The base rates (my lens, since you asked for the distribution)

Calibrated estimates from one-day sponsored AI hackathons:

- **~⅓ to ½ of live demos visibly fail** (wifi, rate limits, auth, latency). Winners come almost entirely from the set whose demo works end-to-end. Ambition correlates *negatively* with winning at 8.5-hour scope; it shows up in the narrative of winners, not their scope.
- **Modal winner profile:** one narrow loop, 2–4 tools, one legible "it just made a decision" moment, ~60–90s of live agent runtime. Not platforms.
- **Matchmade teams underperform** unless the idea splits into 2–3 decoupled workstreams with a typed contract. Ideas needing tight coupling die by 15:00.
- **Partner prizes are softer competition than the grand prize** — most teams bolt sponsor tech on shallowly, so deep authentic usage of one partner's stack is often the highest-EV target. Optimal play: build something that contends for the grand prize but *locks* a partner prize as the floor.
- **Judges reward what they can see.** A Logfire trace tree on screen beats an architecture diagram. "We ran evals" beats "it usually works."

## B. Three ranked candidates

**1. 3AM — on-call incident responder.** A real microservice system breaks on stage; the agent investigates logs/metrics/deploys, forms and discards hypotheses, finds root cause, and rolls back the bad deploy itself. Agentic mechanism: autonomous hypothesis loop choosing its own queries, ending in a *consequential action* (rollback). Beats cliches because something visibly breaks and gets fixed — no chat UI, no documents.

**2. The Auditor — invoice-fraud detective.** Given a pile of expenses, it plans an investigation, cross-references vendors/dates/amounts via tools, and flags the fraud with a structured evidence chain. Deterministic and safe, but weaker compute story and closer to doc-AI cliche.

**3. Walkaway — procurement negotiator.** Agent negotiates against a seller (confederate or second agent) with tool-grounded constraints (margin floor, inventory), and walks away from a bad deal. Flashy, but risks looking like autonomy theater / agents-chatting cliche, and needs a second party on stage.

## C. #1 pick: 3AM

**What it does, in user terms:** It's 3am, production is down, nobody's awake. The agent gets paged, debugs a live system like a good SRE — checking logs, metrics, deploy history, runbooks — and fixes it, then hands you a structured incident report with evidence and confidence.

**Architecture:**
- **Modal (real compute, not hosting):** the target system — 2–3 FastAPI microservices + DB — runs as Modal apps; a "chaos" Modal function injects one of three rehearsed faults (bad config deploy, connection leak, poisoned queue message). Zero third-party APIs anywhere: every tool is your own endpoint.
- **Pydantic AI:** the agent. Tools: `get_logs`, `get_metrics`, `get_deploy_history`, `search_runbooks`, `rollback_deploy`. Output: `Diagnosis(BaseModel)` — root cause, evidence list, confidence, action taken. Validation rejects low-evidence diagnoses → agent must keep investigating (this retry loop *is* the "ship to production" story).
- **Gemini:** Flash-tier model for loop steps (speed on stage), Pro-tier for final root-cause synthesis.
- **Logfire:** every step traced; the live trace tree is projected during the run — simultaneously your "it's really working" proof and your Pydantic-prize lock. Stretch: a 3-scenario × 3-run eval pass-rate slide ("we measured it").

**Hour-by-hour (10:30–19:00):**
- 10:30–11:00 — Spec freeze (one sentence). Three decoupled workstreams with typed contracts: agent core / target system + faults / minimal UI. Smoke-test Gemini, Modal deploy, Logfire trace.
- 11:00–13:00 — Parallel build: target system + fault #1; agent loop with tools; terminal UI showing steps.
- 13:00–15:00 — End-to-end on fault #1; Logfire wired; `Diagnosis` validation loop working.
- 15:00–16:30 — Faults #2 and #3; `rollback_deploy` action; health checks flip green.
- 16:30–17:30 — Record fallback video of the exact demo; cached tool-response replay mode; two full rehearsals.
- 17:30–19:00 — Buffer, submit, rehearse on venue wifi.
- **Cut order:** UI polish (terminal is fine) → fault #3 → rollback action (recommend-only still demos). Never cut the live run + trace.

**3-minute demo script:**
- 0:00–0:20 — Dashboard: real service, red alerts. "It's 3am. Nobody's awake."
- 0:20–0:40 — **Wow amplifier: ask a judge to pick fault 1, 2, or 3.** Inject it live. (All three rehearsed — zero risk, massive credibility against "it's staged.")
- 0:40–1:50 — Agent investigates; Logfire trace growing on screen. Narrate one pivot: "it ruled out the database — watch it check deploy history."
- 1:50–2:10 — **The moment:** it identifies the bad deploy and rolls it back; health checks flip green.
- 2:10–2:40 — Show the structured `Diagnosis` and full trace tree.
- 2:40–3:00 — "Evals, validation, full observability — an agent you'd actually ship to production."
- **Fallbacks:** seeded scenario, temperature 0; cached tool-response mode that still runs the real loop and generates a live trace; pre-recorded video of the identical scenario. Hard rule: if the live run stalls 20s, cut to video without apology.

**Why judges pick it:** the only demo in the room where something visibly breaks and an agent autonomously fixes it; every sponsor's tech used the way that sponsor *wishes* it were used (Modal as compute fabric, Pydantic as the reliability story, Gemini doing real multi-step reasoning); legible in 10 seconds; enterprise-ops angle flatters Conduct. It plausibly sweeps grand + Modal + Pydantic prizes.

**Top 2 killers + mitigation:**
1. **Live latency/variance on stage wifi.** → Fastest fault scenario, Flash-tier model, capped steps, endpoints warmed pre-demo, 20-second cut-to-video rule.
2. **Morning-team coordination failure.** → One-sentence spec, three decoupled workstreams, the `Diagnosis` schema and tool interface as the typed contract agreed by 11:00.

## D. What would change my mind

Evidence that this event's rubric weights novelty/ambition over a working demo, or seeing another team pitch incident response at matchmaking — in which case I take the Auditor (same deterministic skeleton, different skin).
