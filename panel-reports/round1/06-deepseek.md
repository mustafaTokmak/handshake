[0m
> build · deepseek-v4.1-flash
[0m
## A. Cliche list (assume these are taken)

1. Multi-agent "research report" crew (researcher → writer → critic) over a topic.
2. RAG enterprise-knowledge copilot: Gemini + embeddings + "ask your docs."
3. AI SDR that drafts personalized cold outreach at scale.
4. Repo code-review / bug-fixing agent with a diff output.
5. Customer-support triage + auto-reply agent with an eval harness.
6. "Deep Research" clone that browses the web and summarizes with citations.
7. Personal-finance / expense-categorization agent.
8. Travel or event-planning agent that calls flight/hotel tools.

All are single-loop tool-callers or persona pipelines. None have a *mechanism* the judges haven't seen.

## B. Three ranked candidates

**1. GameSmith — inverse mechanism design, in the loop.**
*What:* Given a desired allocation outcome, an agent designs the *rules and payments* of a game so that selfish agents implement it — and then adversarially stress-tests its own design against exploiters.
*Mechanism:* Design → massively parallel simulation → exploit search → credit-assigned diagnosis → patch → repeat. The agent's memory is a rejection archive of failed mechanisms with *why* they failed, which conditions the next generation. Search over mechanisms, not over answers.
*Beats cliches:* Nobody else does game theory. It's a genuine algorithmic idea (implementation theory) with executable ground truth, not a prompt wrapper.

**2. Evolve — self-improving agent scaffold.**
*What:* An agent that optimizes its own prompts, tools, and topology against execution-verified fitness on a task suite.
*Mechanism:* Evolutionary search over scaffolds; Gemini proposes mutations, Modal evaluates populations in parallel, only verifier-passing scaffolds survive; Logfire shows the lineage.
*Beats cliches:* It's meta — the agent improves an agent. Visible fitness curve is a strong artifact.

**3. Falsifier — verifier-first agent.**
*What:* The agent writes an executable specification and property tests *before* solving, then hardens its artifact until a red-team falsifier can no longer produce a counterexample.
*Mechanism:* Critic has an executable obligation (produce a reproducing input), not an opinion. Loop terminates on falsification failure, not on "looks good."
*Beats cliches:* Most "critic agent" demos are vibes; this one is falsification with a witness. Very Pydantic-native. Slightly cliche-adjacent as "test-gen."

## C. #1 pick: GameSmith

**What it does (user terms).**
You describe an allocation problem and a goal — "split 10 GPU-hours across 8 labs, efficient and fair" — and GameSmith outputs a *mechanism*: an allocation rule plus a payment rule. Self-interested labs submit bids; they can lie. The mechanism it invents makes lying unprofitable while hitting near-optimal social welfare. The user never hand-designs the rule.

**Architecture.**
- **Designer agent (Gemini):** emits a mechanism as typed params (allocation rule + payment rule) conditioned on the rejection archive.
- **Simulation evaluator (Modal):** runs thousands of parallel sealed-bid auctions across valuation profiles; the mechanism code executes *inside* Modal so every candidate runs in identical, reproducible conditions. Embarassingly parallel — this is Modal's natural workload.
- **Exploiters:** (a) an **exact best-response solver** (deterministic, exact for the frozen mechanism class) — the ground-truth exploit metric; (b) **LLM strategist personas (Gemini)** that hunt collusion/lying tricks for color and for edge cases the exact solver misses.
- **Diagnostician agent (Gemini):** takes failing generations + attack traces and does credit assignment ("payment rule violates monotonicity at high valuations") → feeds the Designer.
- **Memory:** rejection archive of (mechanism, metrics, reason) — the piece that makes later generations smarter, not just lucky.
- **Pydantic AI + Logfire:** agents and tools are typed Pydantic AI contracts; the mechanism schema is validated for feasibility, budget balance, individual rationality. Logfire traces every generation, attack, and diagnostic — the demo's fitness/exploitability curves *are* Logfire data.

**Hour-by-hour (10:30–19:00).**
- 10:00–10:30 Matchmaking: recruit one optimization/solver person and one frontend person. Team of 3–4 max.
- 10:30–11:00 Scope freeze. Pydantic mechanism schema, sim interface, exact welfare via enumeration (N≤10).
- 11:00–12:30 Deterministic sim + greedy baseline + exact best-response solver. Metrics: welfare gap, exploit gap.
- 12:30–13:00 Lunch.
- 13:00–14:30 GameSmith loop: Designer → Modal grid → metrics → archive. Get generations running end-to-end.
- 14:30–15:30 Exploiter harness + counterexample gate; LLM personas layered on top.
- 15:30–16:30 Logfire wiring + generation-lineage UI (fitness curve, exploit attempts).
- 16:30–17:30 Demo surface: one screen, live replay; **start Modal prod deploy now**.
- 17:30–18:30 Run the long search once, cache every artifact, screen-record fallback, write script.
- 18:30–19:00 Rehearse twice, freeze, opt in.
- **Cut order:** LLM exploiter prose → exact solver only; fairness objective → keep efficiency + exploitability; multi-round → single-shot sealed bid; UI → plain HTML table; second domain → gone.

**3-minute demo script.**
- 0:00 Problem: allocate 10 GPU-hours across 8 labs.
- 0:20 Baseline greedy: welfare = 62% of optimal; one lab lies and captures 5× fair share.
- 0:50 GameSmith proposes mechanisms; Modal runs 5,000 auctions per generation, exploiters attack each.
- 1:30 Fitness + exploitability curves climbing/dropping. **WOW moment.**
- 2:00 Final mechanism: exploiters attack *live on stage* and cannot gain; welfare = 98% of optimal. Show the payment rule it invented.
- 2:20 Kickoff: swap the objective, it designs a different mechanism in 60 seconds.
- 2:40 Close.
- **Fallback:** identical sim code runs on local CPU; all curves cached; pre-recorded capture if Modal or wifi dies.

**Why judges pick it.**
DeepMind is a game-theory/mechanism-design house — an ML researcher will immediately recognize implementation theory and see it's a real idea, not plumbing. It uses every sponsor authentically (Gemini reasons, Modal parallelizes, Pydantic enforces typed invariants, Logfire makes the search legible), shows genuine autonomy and self-verification, and has a measurable before/after. No other team in the room is doing search over mechanisms.

**Top 2 killers.**
1. *LLM bidder noise weakens the strategy-proofness claim.* Mitigation: exact best-response solver is the ground truth; LLMs only narrate and surface edge cases. Report an exploit gap, never "proof."
2. *Search doesn't converge / scope creep.* Mitigation: freeze the mechanism class and N at 11:00; cap generations; pre-run and cache. A loop that honestly finds an exploit, patches it, and improves is still a strong demo.

## D. Change my mind if

The exact best-response and welfare machinery can't be made deterministic and exact for the frozen mechanism class within the first three hours — then pivot to Evolve, whose fitness function is trivially verifiable.
