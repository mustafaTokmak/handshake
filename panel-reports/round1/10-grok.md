**Corrected framing first.** “Find a winning idea” is the wrong objective. You do not control the team (matchmaking at 10:00), competing is optional (opt-in at 19:00), and the prize is credits plus a clap. The judges are vendor engineers standing 8 metres away. The binding constraints, in order, are: **who you stand next to at 09:35**, **whether a demo still runs at 20:02 on venue wifi**, **how much you pre-baked before Saturday**, then idea. Idea is maybe 20% of P(win); team + demo craft + prep are the rest.

**Independent estimates:** ~60 of 70 show up. ~15–18 teams form. **~10–14 opt in and demo** (broken teams quietly skip). One winner, maybe a “best use of X” shout. Baseline P(first) ≈ **7%**. A clean sponsor-stack demo with a rehearsed wow might get you to **12–18%**. Novelty of the idea is a few points on top, not a 3×. EV of prize-hunting is small. EV of looking like the person Conduct/Pydantic/Modal would hire, or the founder an investor remembers, is larger. **Play: pre-build a world, recruit at the door, use 19:00 as a real quality gate, treat the prize as upside.** If the team is a dumpster fire at 11:00, join a stronger one or skip opt-in and spend the evening on sponsor conversations. Do not die on an idea.

The vehicle below assumes you arrive with keys, a seeded fake company, and a skeleton. Greenfield with strangers in 8.5 hours is how you become cliche #1 with a broken demo.

---

**A. Cliche list**
1. RAG support bot over PDFs / “chat with your docs.”
2. Meeting notes → action items / calendar agent.
3. AI SDR / outbound email personaliser.
4. Multi-agent “company of agents” that only talk to each other.
5. Travel / night-out planner.
6. GitHub code-review copilot.
7. Live browser-use booking agent (restaurant/flight) — dies on stage wifi.
8. Voice receptionist / call-centre agent.

---

**B. Three ranked candidates**

**1. Airlock** — typed change-control OS for a fake internal app: messy request in, nothing executes until plan → simulate → policy rewrite → human stamp.  
*Agentic:* it resolves entities, computes blast radius, **refuses or rewrites** the user’s request under policy without being asked, then applies only the stamped plan.  
*Why not cliche:* the product is the operating system (Conduct’s thesis), not a chatbot that “does the task.”

**2. Whiteboard Compiler** — photo of a process on a whiteboard becomes a running Pydantic AI workflow deployed on Modal.  
*Agentic:* Gemini vision extracts steps/roles/tools; the agent binds tools, fills gaps, deploys, runs one live job.  
*Why not cliche:* DeepMind multimodal flex, visible compile. Weaker: vision flake, thinner Conduct story.

**3. Hypothesis Farm** — paste a failing job log; agent proposes N root-cause hypotheses; Modal workers test them in sandboxes in parallel; typed verdict + patch.  
*Agentic:* it chooses which hypotheses to test, kills dead ones, writes a patch only if tests pass.  
*Why not cliche:* Modal is the demo. Weaker: looks like a DevOps toy and duplicates half the room’s “agent debugs code” instinct.

---

**C. #1 — Airlock**

**What it does.** You are IT at **Northwind Analytics**. Input is a messy Slack screenshot or paste: *“add the whole Berlin office to the Finance dashboard and make Lena admin.”* Airlock does not do it. It resolves Berlin → 14 people, Finance dashboard → ACL, Lena → identity; computes blast radius; **policy-rewrites** to “Berlin as viewers, Lena admin only via a staged ticket”; shows the diff; you stamp; SQLite IAM updates; undo exists. The user-visible object is a **change ticket with a red refusal**, not a chat transcript.

**Architecture**
- **World:** local SQLite — employees, orgs, resources, ACLs, policy YAML. No OAuth. No real SaaS.
- **Pydantic AI:** one `ChangeAgent` with `output_type=ChangePlan` (typed intents, targets, diffs, risk, rewritten plan). Tools: `directory.search`, `iam.get`, `iam.diff`, `policy.evaluate`, `iam.apply`. Logfire is the courtroom transcript — every tool span on a second monitor.
- **Gemini:** (1) screenshot/text → structured `Intent`, (2) planner/replanner inside the Pydantic AI loop. Use the model they’re handing out; do not fine-tune anything.
- **Modal:** `simulate_change.starmap` over affected identities/resources; returns would-be ACLs + conflict flags. This is the only “compute.” Cold-start cached at 18:00.
- **UI:** two panes — requested vs rewritten plan, blast-radius numbers, Stamp / Reject. Streamlit is enough. Logfire link next to Stamp.
- **Not Conduct’s API** (you likely won’t get one). It is a parody of their category on purpose, labelled as such in the first sentence of the pitch.

**Hour-by-hour (10:30–19:00)**  
This is integration day. If you have no skeleton, cut to text-only + local simulate by 12:00 or you will demo a chatbot.

| Time | Work |
|---|---|
| 10:30–11:00 | Lock scope. Clone skeleton / scaffold. Keys in env. Seed DB. One presenter, one agent, one UI. No new features. |
| 11:00–12:30 | Tools + `ChangePlan` schema + happy path on **one** canned text request. |
| 12:30–13:00 | Lunch. Presenter writes the 3-minute script. Agent stays on the loop. |
| 13:00–15:00 | Policy rewrite that **refuses bulk admin**. Screenshot → Intent if time. |
| 15:00–16:30 | Modal fan-out simulate. Logfire spans named after tools. Cache one full run. |
| 16:30–17:30 | UI: requested vs rewritten, numbers, Stamp, before/after ACL. |
| 17:30–18:15 | Rehearse twice. Record fallback video of the Logfire trace. Freeze fixtures. |
| 18:15–19:00 | No new code. Opt in only if Stamp still mutates the DB on the laptop. |

**Cut first when behind:** (1) screenshot → paste text, (2) Modal → local `simulate()` still returning the same schema, (3) Streamlit chrome, (4) undo, (5) second scenario. **Never cut:** typed plan, policy refusal, Stamp, Logfire screenshot.

**3-minute demo**
- 0:00–0:20 *“Enterprise agents don’t fail because they’re dumb. They fail because they execute. This is an airlock.”*
- 0:20–0:40 Drop the Slack screenshot (or paste). Gemini extracts Intent on screen.
- 0:40–1:20 Agent runs. Tool names tick. **Wow (1:10):** banner **REFUSED: bulk admin on Finance.** Rewritten plan appears: 14 viewers, 1 staged admin. Blast radius 14 → 1 privilege change.
- 1:20–1:50 Flip to Logfire: planner → search → diff → policy.evaluate → rewrite. Let a Pydantic person see their product.
- 1:50–2:20 Stamp. ACL table updates live. Mention Modal simulations (or show the cached parallel results panel).
- 2:20–2:50 One line each: Gemini structured intent, Pydantic AI + Logfire as the OS, Modal for blast-radius fan-out, Conduct-shaped control plane. Stop talking.
- **Fallback:** if wifi dies, play the 45s screen recording of the same refusal + Logfire, then hit Stamp against **local SQLite** (that path never needs the network). If Gemini dies, load `fixtures/intent_berlin.json` and still run tools. If Modal cold-starts, show `fixtures/sim_berlin.json` in the same UI slot — same schema, labelled “cached sim.”

**Why judges pick it.** Everyone else ships a helpful intern. You ship the missing OS: **the agent decides not to comply.** DeepMind sees structured extraction + tool loop. Pydantic sees typed `ChangePlan` and a gorgeous trace. Modal sees real fan-out, not a billed hello-world. Conduct sees their category enacted, which nobody else will bother to understand. It also survives a stranger team because the wow is a seeded policy, not a model miracle.

**What kills it**
1. **Team hijack toward a chatbot.** Mitigation: 09:30–10:00 recruit with the working skeleton on your laptop; if they insist on a wrapper, join a different team or keep Airlock as a 2-person fork. Do not “merge ideas.”
2. **Live loop nondeterminism / timeout on stage.** Mitigation: freeze the canned Berlin request; fixture the Intent; cache Modal; Stamp is local. The live call is optional garnish.

---

**D.** I would abandon Airlock if Conduct ships a usable sandbox API on the day — then build **on their OS**, not a parody — or if your actual teammates are already multimodal researchers with a working whiteboard-to-agent path at 10:15; ride that, don’t fight them.
