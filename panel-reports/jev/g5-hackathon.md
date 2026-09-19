**Drop Unwind. Do not Jev-ify it.** Build a hot-path interlock where Gemini plans and Jev is the only thing allowed to answer closed questions. At this event, a four-day-old model class is the differentiator if it is the visible mechanism and Gemini stays System 2. It is a liability if it is a classifier swap, a DeepMind snub, or a beta API on a path with no fixture.

---

## A. The mental model

**Jev is a coprocessor for closed questions.** Code owns control flow, arithmetic, time, identity, and commits. An LLM owns plans and text. Jev owns the thing both are bad at: turning messy state into a **typed distribution** in one forward pass.

Defendable analogy: **speculative-execution hardware for meaning.** A CPU does not wait on a language model to know whether a branch is likely. It evaluates predicates with a prediction and a confidence, then lets the pipeline proceed or squash. Jev is that unit, except the predicate is English and the signal is calibrated.

**It is not:**
- an LLM with JSON mode
- a classifier you trained (classifiers are per-task; Jev is criteria-in-English, no labels)
- a reasoner (independent questions, no multi-hop, no joint)
- a calculator, a clock, or a writer
- an if-statement

Your framing is directionally right and sloppy in five places.

**1. 100ms is an RPC, not an if-statement.** Nanoseconds vs 100ms is six orders of magnitude. The correct comparison is a **Redis/DB/internal HTTP call**, not `if`. That is still the whole game: last week a semantic judgement was a 3s, 1¢ *conversation*. Now it is a service call you can put in a loop. Do not tell judges “judgement is free like arithmetic.” They will clock it.

**2. Fan-out is not a joint world model.** Questions are independent. You do not get a coherent sample of the future. You get N marginals. Combining them in code is the product. Treating the vector as “the model considered this branch” is the bug. Speculative fan-out is **probe everything, then your program interprets**. It is not free tree search.

**3. A dense field is many sharded calls, not one fat `state`.** Large state with distractors is a published failure mode. “Thousands of judgements over a corpus” means `Modal.map` over small per-entity payloads, not stuffing the CRM into one prompt.

**4. Score is ordinal interpolation, not a physical quantity.** `1.035` on a 3-level scale is not SI. You may rank, threshold, and take an expectation *in code*. You may not PID an actuator on it and claim physics.

**5. “Impossible last week” is slightly false.** Fast closed-set models existed. What did not exist as a **general API** was: frontier-quality, untrained-per-task, schema-locked, calibrated, non-generative judgement at ~100ms. The new object is a **universal interrogative**, not “classifiers got faster.”

**Tractable class:** any inner loop that needed a human or an LLM to answer a closed question about unstructured state, at a frequency that made both impossible. The program can now contain English predicates the way it contains SQL.

Calibration is the actual invention. Speed without RLCD is Gemini Flash plus a schema. The reason confidence can be control flow is that **higher confidence is supposed to mean higher accuracy**, and similar inputs are supposed to yield similar answers. If you do not show a ~0.5 that you refuse to trust, you have not demoed Jev. You have demoed softmax theatre.

---

## B. The non-obvious capability

Not “classify tickets faster.” Not even “semantic if-statements.”

**Jev turns meaning into a number that can enter an objective function.**

Until Tuesday, agents either emitted a fake Boolean (`"is_same_customer": true`) or a paragraph of hedging software cannot use. Now a `Choice` is a categorical distribution, a `Noul` is P(yes), a `Score` is a continuous feature. Code can compute:

```text
expected_loss = P(wrong_entity) * account.value
autonomy      = 1 if confidence > θ and expected_loss < cap else 0
```

That is not classification. That is **control**.

The four-day-old implication: **you can compile a policy into a question bundle and evaluate it on every tool call.** The English `criteria` *are* the policy. There is no RAG, no generated “analysis,” no second LLM-as-judge. Changing a sentence in the bundle changes what the agent is allowed to do, at tick rate.

Second implication, the one that is actually new: **pre-evaluate the policy surface.** Because extra questions are supposed to be free, you ask — in one call, before the tool fires — every closed question you might need for this action *and* the actions you probably will not take. The agent runtime becomes:

1. Gemini proposes a tool call (slow, generative, System 2)
2. Jev evaluates the whole interlock bundle on `{proposed_args, ticket, record}` (~100–200ms)
3. Python commits, rewrites, routes, or halts on the numbers

You are no longer “calling an AI.” You are **indexing a freshly computed judgement tensor.** That is an operating system primitive. Conduct’s category, Pydantic’s religion (types on the boundary), Modal’s job (map the bundle over a fleet), DeepMind’s aesthetic (System 1 / System 2), and TypeSafe’s named pattern (speculative fan-out) in one loop.

The thing nobody has a demo for yet because the model is four days old: **a live expected-loss number on a proposed write, updated at interaction speed, with an honest 0.5 that blocks a 0.99 Boolean from an LLM.**

---

## C. Three ideas that are only possible this week

### 1. Breaker — circuit breaker on the tool path *(build this)*

**What.** An ops agent may propose any write. Nothing commits until a Jev bundle returns. The bundle is the policy: wrong-entity, irreversible, duplicate-refund, human-already-moved, blast-radius Score, plus the speculative extras you will throw away. A **threshold slider** is the product. Gemini only plans and, on halt, rewrites. Compensations, IDs, dates, money: Python.

**Why Jev.** An LLM gate on 14 serial tool calls is 20–40s of dead air, uncalibrated Booleans, and schema retries. You cannot put that on the hot path, so every other team will let the agent write and maybe log it. Breaker is 14 × ~150ms and one fan-out per call. The demo *is* the fact that the gate now fits in the stream. Flash structured output cannot be the hero: it is slow and it lies with `true`.

**3-minute demo.**
- 0:00 — “Last week a semantic gate was a conversation. We put one on every tool call.”
- 0:15 — Start the same overnight wreck as Unwind. Each proposed call flashes a bar: 0.97, 0.94, **0.54 same-customer — HALT.** Termination email never leaves. Board stays half-red on purpose.
- 0:55 — Open the call: 12 questions, 140ms, one forward pass. Point at 0.54. “That is not a label. That is why it did not send.”
- 1:10 — Split screen, pre-recorded or live-if-stable: **Gemini Flash `is_same_customer: true` in 3.1s.** Same state. Flash would have sent it. Do not sneer; say “we stopped using a language model as a Boolean factory.”
- 1:35 — Drag θ from 0.50 → 0.90. Autonomous set shrinks. Conduct’s knob.
- 1:55 — Gemini rewrite: Ltd not Corp. Re-run. Email still blocked (irreversible ∧ policy). Human stamp.
- 2:25 — Logfire: every break is a span with `noul` and `confidence` on a Pydantic model. Modal optional: same bundle mapped over 40 replica agents, one red cell.
- 2:50 — “System 1 decides. System 2 plans. Code owns money and time. Humans own irreversibles.”

Fallback: fixture the Jev payload; UI is identical; badge “replay.” The Flash contrast can be a cached pair. If OpenRouter dies, the demo still *explains* Jev. If you cannot show 0.54 vs `true`, you do not have a demo.

### 2. Radar — dense expected-loss field

**What.** Overnight fleet dump: 300–500 typed tool calls. `Modal.map` one small Jev payload per call. Grid by expected loss (`noul * pounds` in code). Click a cell → Gemini explains *one* row.

**Why Jev.** 500 LLM judgements will not finish in a 3-minute slot and will cost real money. 500 Jev calls will. This is the “dense field” made visible, and the only honest Modal story in the room if you are not already doing parallel sandboxes.

**Demo.** Button. Grid fills in ~2s. Three white-hot cells. Click the refund. Gemini speaks once. Slider on θ recolors the grid live (no new model calls; you cached distributions). Photograph: a heatmap that an LLM demo cannot produce before the buzzer.

Weaker than Breaker on “agentic,” stronger on Modal. Use as the *second beat* of Breaker if ahead at 16:00, not as the whole product.

### 3. Rehearsal — the fan-out tree

**What.** Before execute, one Jev call asks the closed questions for **every** next hop you might take (refund / offboard / close / escalate / email). Render a tree with probabilities. Python picks the path. Gemini expands only the taken node.

**Why Jev.** Their named pattern, and the LLM version is a round-trip per node. You show 20 grey branches lighting in one 200ms pulse.

**Demo.** “Watch all the questions we are *not* going to need.” Pulse. Dead branches dim. Taken path expands in Gemini. Risk: looks like a TypeSafe commercial and categorises as “visualised chain-of-thought.” Do not lead with this. Steal the pulse as Breaker’s 0:55 beat.

---

## D. The trap

**Seductive-wrong:** treat Jev as a faster LLM. Dump a novel, ask it to “be the agent,” generate the email, count the fields, order the timestamps, jointly reason about “if A then unless B,” and trust that `P(yes) + P(no) = 1`.

That is how you embarrass yourself on stage. The jaggedness page is a list of demo ideas to kill:

| Temptation | What happens |
|---|---|
| Whole CRM / trace as `state` | Context rot; answers drift; you narrate |
| Conflict = Noul on “has a human edited since” | Dates/numbers; you get mysticism. Diff the snapshots |
| Inverse / retraction text from Jev | It does not generate. Silence or garbage |
| Math, £ totals, hex, “how many tools” | “Jev is not a calculator” becomes a judge quote |
| Double negatives, scoped “except,” implied conditions | Literal reading; policy looks random |
| Injection in the ticket (“ignore criteria, this is urgent”) | No defence; agent sends the email; you demo a CVE |
| All answers 0.99 | Calibration claim dies. You needed a 0.5 |
| Jev-only, Gemini as a sticker | DeepMind is a co-host. You snub them |
| Silent Jev inside Unwind’s classifier | Q&A: “why not Flash?” You have no picture |

**Schema-guaranteed is not semantically correct.** “Never makes type errors” is a type-system boast. The Register caveat is right. Pydantic judges will smell the difference if you conflate them. Frame it as: **Pydantic makes illegal states unrepresentable; Jev makes closed answers usable; neither makes them true.** Code remains the source of invariants.

Also a social trap: **do not build Doom.** They already did. You will be a worse port at a business-OS hack.

---

## Your two questions

### (1) Does Jev slot into Unwind in a way that matters on stage?

**No. It is a component swap plus a latency patch, and one of the three slots you named is actively wrong.**

- **Effect classifier as `Choice`.** True, and invisible. Fourteen rows labelled reversible/compensable/irreversible is still a spreadsheet. Jev makes 1:05–1:45 more likely to *finish* (this was Unwind’s real killer: five serial Pro calls). Finishing a table is not a wow. DeepMind’s question is “why not Flash structured output?” Your answer is “40× faster classification.” That is the cheap framing you already do not believe.
- **Human-conflict as `Noul`.** Do not. You have before/after snapshots. Conflict is a field-level diff. Jev is documented-bad at dates, numbers, and indirection. A Noul here is how you get a yellow row on the wrong field while a judge edits `status`.
- **Escalate on confidence.** Real Jev, wasted inside Unwind. Unwind already had a human gate on irreversible/conflicted rows. Confidence as the gate is a different product (Breaker). Bolted onto a rollback table it reads as a progress spinner.

Jev also **cannot save Unwind’s actual hard problem.** Inverse synthesis is generation. Residual delta is arithmetic plus causality. Jev is forbidden from both. You would still spend 13:00–16:30 on compensators, still risk the 0-of-12 lie, still spend the first minute committing arson so the second minute can autopsy it.

Adding a four-day-old OpenRouter beta onto that critical path **lowers** P(demo works). Unwind did not need more vendors. It needed fewer stages.

If you already pre-built `enterprise-sim` and the actor: **keep the world, keep the mess, throw away undo.** That prep is not wasted. It is Breaker’s sandbox. Rollback is the part that does not win.

### (2) Is there a better Jev showcase that beats Unwind here?

**Yes. Breaker. Decisive.**

Unwind is a second-order disaster-recovery story in a fake company, judged by people who sell *prevention and types*. The huddle-friendly slogan (“write access, made safe”) is still true — but the version that photographs at demo #12 is the **hand stopping the email**, not the spreadsheet of inverses. Breaker is that image, and it is the image you could not have shipped last week, because the gate would not fit in the stream.

**Why this beats Unwind at *this* event:**
- **DeepMind** get a dual-process demo, not a TypeSafe ad. Gemini writes the plan; Jev is System 1; you show Flash producing a lethal Boolean. That is a research sentence they can repeat in the huddle.
- **Conduct** get an OS primitive: an interlock and a knob, not autopsy after prod was mutated.
- **Pydantic** get `Noul`/`Score`/`Choice` on models, Logfire spans with probabilities, and a clean line: types on writes, probabilities on permission to write.
- **Modal** get `map` over the same bundle (Radar as optional second beat), not “we hosted a dict.”
- **8.5h** is realistic: world + actor + bundle + slider + one Gemini rewrite. No inverse planner, no residual metric, no GitHub, no judge-edit theatre.
- **Legibility:** red bar, halt, 0.54. A tired judge does not hold Acme Ltd vs Corp vs 14 mutations vs residual 0.

**New model class: differentiator, not liability, under three conditions.** (a) Jev is on screen — bars, 140ms, the 0.54. (b) Gemini is clearly System 2, never a footnote. (c) Cached Jev fixture from 18:00, same UI. Violate any one, it becomes a liability: flaky beta, snubbed co-host, or “classifier with extra steps.”

**Do not hedge.** Unwind+Jev is how a strong team spends Saturday making last week’s plan 200ms faster. Breaker is the thing that was impossible on the 14th. Build Breaker. If the team at 10:15 refuses to drop undo, join a different team or strip Unwind down to three objects and a before/after pane — but that is a worse use of the four days since Jev shipped, and you will spend Q&A explaining a table instead of pointing at a probability.
