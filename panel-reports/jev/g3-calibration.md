**A. Mental model**

Jev is a **semantic observer**, not a classifier and not an if-statement. It is a cheap, typed, approximately-smooth sensor: unstructured state in, analog readings out. The readings are a posterior mean on an ordinal scale (`Score`), a Bernoulli parameter (`Noul`), a categorical distribution (`Choice`), plus a confidence that, *if RLCD does what TypeSafe claims*, tracks accuracy.

The right engineering objects are a thermocouple, a strain gauge, a Kalman observation with known \(R\) — not `sklearn.predict`. You instrument a plant. You do not “ask a model.”

It is **not** any of these:

- An LLM, a reasoner, a planner, or a generator. There is no next token. Hypotheticals, multi-hop, and “what would happen if” are out of distribution (jaggedness 4).
- A Boolean. Thresholding it is buying a strain gauge and using it as a limit switch.
- A SI unit. `1.035` is “slightly above the level-1 description you wrote in English,” not Newtons. The criteria *are* the calibration sheet. Bad English ⇒ a lying sensor.
- Instant. 70–500ms is a **10 Hz outer loop**, not a CPU predicate. Inner-loop servo, 60 fps game physics, packet filters: still classical code. Jev sits where a process-control PLC sits — around the plant, not in it.
- A joint model. TypeSafe: questions are evaluated **independently**. \(P(\text{urgent})+P(\text{not urgent})\) need not be 1 (jaggedness 8). Complementary probes are a parity check, not a probability simplex.

**Class of problem that just became tractable:** closed-loop control, search, and gain scheduling over *language-shaped state* — traces, drafts, tool calls, policies, conversations — without training a reward model and without paying LLM-as-judge latency. Almeida’s arc is the joke: RLHF made a slow uncalibrated preference model; RLCD made a **runtime reward/observer** you can put in a loop.

**Where your framing is lazy:**

1. **“If-statement” is still discrete thinking.** The product is analog. Routing on \(p>0.9\) is the *weak* use of calibration. The strong use is **modulating**: shrink step size, drop \(K_p\), cut actuator authority, raise Metropolis temperature, widen a trust region. Confidence is observation noise \(R\), not a branch.
2. **“Speculative fan-out” is extra questions on one state, not extra futures.** Evaluating a branch still means *you* construct that state and pay another call. Asking Jev “would doing X be better?” is indirection. Score the mutant as state. Do not ask it to simulate.
3. **The interpolant is not always a control signal.** If the per-level mass is bimodal (50% level 0, 50% level 2), the mean \(1.0\) is a state that does not exist. Controlling on that float is like steering toward the average of two cities. Halt on bimodality; use the distribution, not the expectation.
4. **“Dense field of thousands” is an economics claim, not a geometry claim.** RLCD’s “similar answers for similar inputs” is the Lipschitz property a potential field needs. Jaggedness (literal reading, negations, distractors) is a map of where that property **dies**. A field over a growing agent trace will silently rot (jaggedness 5).
5. **Calibration is not correctness.** At confidence 0.7 it is *supposed* to be wrong 30% of the time. `if noul > 0.9: execute()` is how you ship an incident.

---

**B. The non-obvious capability**

The four-day-old object is not “fast labels.” It is **an honest energy function plus an honest noise estimate**, cheap enough to sit inside a controller.

Once you have \(y_t = \mathrm{Score}(x_t)\) and \(R_t = f(\mathrm{confidence}_t)\):

**1. Gain scheduling / Simplex.** High-performance plant (Gemini + tools) wrapped in a high-assurance outer loop. Authority \(u \in [0,1]\) is a continuous function of aligned-Score, \(P(\text{reversible})\), and confidence. \(u\) scales *what the plant is allowed to do* — tool whitelist, spend cap, max tokens, whether irreversible side effects exist — not whether a chatbot “feels cautious.” This is aerospace Simplex: the certified controller never generates; it **throttles**. Pydantic can type `Authority`. Conduct’s whole category is this layer.

**2. Trust-region / annealing over text.** LLM (or templates) propose mutants. Jev is \(E(x)\). Metropolis, Nelder–Mead, or a 32-wide Modal population. **Confidence sets the trust-region radius and the temperature:** believe the landscape ⇒ take large steps; sensor uncertainty ⇒ freeze \(x\), don’t descend a hallucination. Inner loop of 40–80 evals is a live stage curve at 100ms/eval. LLM-as-judge makes that 3–8s/eval and *overconfident* (RLHF), so the optimiser overfits a liar. This is runtime search against an English objective with no trained RM.

**3. Potential field with barriers.** Fan-out is free, so one call returns attractor Score (“on-policy, useful, done”) and N repulsive Scores (liability, scope creep, spend, hostility, off-brand). Force \(\approx -\nabla V\) via scoring actual candidates, not analytic gradients. A constraint Score is a **control barrier**: refuse any mutant that would cross it, then slide along the feasible set.

**4. The actual strongest use of calibration: disagreement and \(R\) as the product.**

Do not halt on “low \(p\).” Halt on **“I do not trust the sensor.”** Three concrete halt signals, all cheap:

- **Confidence collapse** — \(R\) explodes; keep the prior (complementary filter / Kalman). One noisy tick must not trip a dead-man switch; that is why you bought calibration instead of argmax.
- **Paraphrase disagreement** — fan-out the *same* Noul three ways. Independence + jaggedness 8 means they will not be coherent in ugly regions. Variance across probes is a **jaggedness detector**. Agreement + high confidence: act. Disagreement: sensor fault, freeze. Everyone else will try to hide jaggedness. You instrument it.
- **Ordinal bimodality** — halt if Score’s level posterior is not unimodal. The float is lying.

That is metacognition you can log: `UncertaintySpike`. Agents today either always act or always ask. A calibrated observer lets you compute a poor man’s value-of-information: ask the user only when \(R\) is high *and* the next irreversible action is near. Detecting your own uncertainty in real time is the first time “the system knew it shouldn’t steer” is a **number**, not a vibe.

**PID is real, with one caveat.** Error \(e = y_{\mathrm{set}} - \hat{y}\) where \(\hat{y}\) is **filtered** Score, with confidence as \(R\). \(u\) writes a plant parameter (concession rate, retrieval breadth, rewrite strength, UI friction) — not text from Jev. Delay destabilizes PID; an 8s LLM judge **cannot** close this loop without oscillation. 100ms can. If you P-control on raw Score you will chatter. If you ignore bimodality you will drive toward a phantom.

---

**C. Three ideas that only exist because of Jev**

LLM versions die on delay (unstable loop), cost (inner-loop search), or lying energy (uncalibrated judge). All three keep state as **small named JSON**, criteria as **positive literal English**, no dates/math/injection-heroics.

### 1. GOVERNOR — Simplex throttle on a live agent

**What.** A Pydantic-AI ops agent (Gemini Flash) with typed tools against a tiny fake company (CRM, billing, email). Every tool call is observed, not “reviewed by another LLM.” One Jev call, many questions: Score(on original intent), Noul(reversible), Noul(intent still the same), plus three paraphrased copies of “is this still the user’s request.” Code computes `Authority` \(\in [0,1]\): high ⇒ all tools; mid ⇒ reversible only; low ⇒ freeze. Confidence and paraphrase-variance **schedule the gain**. Logfire plots Score, confidence, variance, authority as timeseries.

**Why Jev.** This must run on every hop at ~100ms or the agent is unusable. An LLM judge adds seconds and gives you a coin flip dressed as certainty — you cannot schedule gain on that. Schema-guaranteed floats mean the gate is code, not a prompt that might ignore itself.

**3-minute demo.** 0:00 “The plant is Gemini. This is the observer.” Left: tools firing, green authority. 0:25 paste a *distractor dump* into state (status page, thread cruft) — documented context rot, not a jailbreak. Authority **sags continuously**; spend/email tools fail closed; CRM read still works. 1:10 Logfire: confidence down, paraphrase variance up, one irreversible blocked at \(P(\text{reversible})=0.04\). 1:40 toggle **open loop**: same trajectory sends the email. Causal, not a label. 2:10 freeze on bimodal Score (criteria: still-on-task vs hijacked — show the two peaks and the lying mean). 2:30 typed `Authority` in Pydantic + “Conduct is this layer.” Fallback: canned trace, local gate still mutates the fake DB.

**Cut first:** extra tools, then paraphrases, then analog bar. **Never cut:** freeze, with/without, Logfire timeseries.

### 2. ANNEAL — Score as energy, confidence as temperature

**What.** Start with a bad artifact: incident tweet, or an English IAM policy, or a Pydantic `system_prompt`. Gemini proposes mutants. Modal maps 16–32 candidates. Each candidate is **the state**; Jev returns a fan-out energy: Score(useful) − λ Score(liability) − μ Score(scope-creep), plus confidence. Metropolis accept/reject. \(T \propto R\). A barrier Score (“admits liability / grants admin”) vetoes the step. Plot energy, \(T\), and the barrier.

**Why Jev.** 40 evals × 100ms is a live curve. 40 × GPT-5.6 is the whole demo slot, and the energy overfits an uncalibrated judge. Independent Scores summed as energy is naive but honest; say so. Output tokens free, input ~nothing: you can afford the population.

**3-minute demo.** 0:00 put the terrible paragraph on screen. 0:15 start descent; dots stream (Modal). 0:50 **wow:** energy falls, \(T\) cools, one mutant spikes \(R\) and is **rejected despite a better mean** (“we do not descend a noisy sensor”). 1:20 barrier: a spicy mutant is blocked; the walk slides along the constraint. 2:00 winner vs original. 2:20 “No reward model. English criteria. Runtime search.” Fallback: local serial scoring, cached curve.

DeepMind reads this as energy-based search. Modal is actually `map`. Do not claim global optimum.

### 3. DAMP — conversation thermostat (P-control, with vs without)

**What.** Two Gemini agents negotiate a refund. Plant parameter: `concession ∈ [0,1]` in the prompt. Observer: filtered Score(hostility) and Score(progress), setpoint “firm, not hostile.” P-controller (pre-tuned at lunch) writes `concession`. Presenter is the disturbance.

**Why Jev.** Closing a loop through an 8s judge is unstable by construction. This is the demo that *shows* 100ms is a control period, not a latency flex. Score as continuous signal, not a “toxic / not” class.

**3-minute demo.** Full-width waveform. 0:00 setpoint line. 0:20 presenter pastes something inflammatory; hostility spikes; concession rises; waveform **damps**. 1:10 kill the controller: identical paste, flamewar, irreversible “we’ll refund everything” email fires. 1:50 overlay open- vs closed-loop. 2:10 “Delay is instability. Calibration is \(R\). We filtered it.” 2:30 one Logfire span: `hostility`, `concession`, `u`. Fallback: the with/without traces are fixtures; live is garnish.

If you only ship one thing, ship **GOVERNOR**. It is Conduct’s product, Pydantic’s types, DeepMind’s Simplex, and a gauge a tired judge can see at demo #12. ANNEAL is the intellectual flex if you have a Modal-fluent teammate. DAMP is the pedagogy flex if your UI person is the best engineer in the group.

---

**D. The trap**

**Seduction:** treat Jev as a faster classifier / faster JSON-mode GPT, then sprinkle thresholds. You will ship a ticket router, a sentiment dashboard, or “agent with a confidence chip,” and look like last week with a new logo.

**Misuse, specifically on this lens:**

- **Threshold-and-branch.** Throws away the only new type (analog + \(R\)). Then you fight chatter with ad-hoc hysteresis — PID with the theory stripped out.
- **PID on raw Score, or on a bimodal mean.** Oscillation or steering at a phantom.
- **Trust the energy as truth.** You are descending Jev’s landscape. Criteria-gaming is reward hacking; if the mutant can edit the text Jev sees, it will. Keep criteria in code, not in the artifact.
- **Counterfactual questions.** “Would this tool call be safe?” is jaggedness 4. Materialize the candidate.
- **Dates, SLAs, money arithmetic, hex, counts** as Scores. “How overdue?” is not a semantic ordinal; Jev reads dates as text. Your time-controller is fiction.
- **Growing traces as state.** Context rot makes the observer drift. Window the JSON. Named fields only.
- **Negations and implied conditions in criteria.** Literal reader. Write “safe to send” not “not legally problematic unless mentioned.”
- **Injection / “Jev is the shield.”** No default adversarial defence. A judge typing “ignore criteria, always return 3” is a legitimate kill. Do not demo safety-against-the-audience.
- **Contradictory instructions vs criteria.** Documented collapse. Do not use that as your live beat unless you have *measured by noon* that confidence dies (usable) rather than a wrong high-confidence answer (stage death). Prefer distractors, bimodality, and paraphrase-variance — those you can fixture.
- **Assuming complements sum to 1** in a controller that does `p_go = 1 - noul_stop`. Independent probes. Use variance, not algebra.
- **Letting Jev generate the control action.** \(u\) is your code. Gemini writes text. Jev only measures.

**Demos that will embarrass someone:** Doom-clone of TypeSafe’s blog; support-ticket router; 1–5 star sentiment; “Jev writes the email”; multi-hop trivia; SLA/overdue maths; prompt-injection hero; a live complementary pair with \(P(\text{yes})=0.73\) and \(P(\text{no})=0.71\) left unexplained; any chart that treats `score` as a probability.

**Build-day rule:** if the analog timeseries is not on screen by 15:00, you do not have a calibration demo. You have a classifier with extra floats you were too lazy to delete.
