**The primitive is a type-directed product measure.** One non-autoregressive instruction:

`PROBE : State × (Name ⇀ FiniteType) → ∏_i Δ(τ_i)`

You declare the types first. The sampler inhabits them all in one forward pass. Extra coordinates are free. Each coordinate is a calibrated distribution, not a token string, not a bool, not a joint.

Name it **`PMatch`**: probabilistic, parallel, schema-compiled `match`. The nearest machine instruction is SIMD compare / GPU predication, not `CALL llm` and not `IF`.

---

## A. What it is

A classifier has a fixed `Y` baked into the weights and is used as `argmax`. An LLM inhabits `String` and hopes you can parse. Jev inhabits a **user-supplied finite type**, at inference time, and returns the **measure**.

Three inhabitants, one exponential family:

| Primitive | Type τ | Object returned | Honest reading |
|---|---|---|---|
| Choice | finite set | categorical `Δ(τ)` | a **named simplex** |
| Score | ordered chart `{0..k-1}` | `Δ(levels)` plus a float | **posterior mean on an axis you drew in English** (`1.035` is a barycenter, not a probability) |
| Noul | `2` | `p ∈ [0,1]` | **Bernoulli parameter**, `P(yes)` |

Training (RLCD) is a proper scoring rule on those objects: confidence tracks accuracy; similar states map to similar measures. That is why the output is usable as a number in *your* algorithms, which LLM logprobs never were.

**The independence clause is load-bearing.** Questions are evaluated independently given state. The API returns a **product of marginals**, not a joint. You did not get a Bayesian network, a CRF, a consistent random field, or `P(A ∧ B)`. You got a **named feature map** `φ(s) ∈ [0,1]^n` (plus ordinal means) whose coordinates are separately calibrated.

So the object is:

1. **Not a classifier.** The label set is part of the query. The value is the simplex. Fan-out makes it a query language, not a single map `X→Y`.
2. **Not a differentiable `if`.** You cannot backprop through the API. You *can* use `p` as a gate or a mixing weight. Type of an `if` is `Bool`. Type of Jev is `Measure`.
3. **Not a compiled program.** The schema is a runtime layout, like a GPU framebuffer: you declare the buffer, one dispatch fills every channel. Semantics are interpreted; **layout is compiled** (ill-typed outputs are unrepresentable).
4. **A learned oracle in the complexity-theory sense**, with a published domain of partiality (the jaggedness list). Cheap, typed, probabilistic, **not total**.
5. **A naive-Bayes featurizer with English coordinates.** Joints, arithmetic, dates, copulas, control flow, and generation stay in your process.

**Sharpest analogy I will defend:** it is a **GPU for predicates**. Bind state as the texture, declare a framebuffer of finite types, one dispatch, every pixel is a calibrated probability. You do not rasterize a paragraph.

Second analogy, same object: **`SELECT` where every projection is an English predicate and the cell type is `probability`, vectorized.**

**What it is not:** a reasoner, a generator, a calculator, a temporal-logic engine, an agent, a structured-extraction model (open strings, IDs, dates, names are not finite types), a joint world model, or an `if`. Calling it a “fast classifier” is what you get if you `argmax` and throw the product in the bin.

**Class of problem that just became tractable:** closed-world semantic *measurement* at request-handler and corpus-scan frequencies, where the ontology can be named up front, sequential logic lives in code, and you need numbers that can enter an index, a heap, a threshold, or an expected-value sum.

---

### Where your framing is right, and where it is lazy

**Right:** schema-guaranteed; probability is the product; Score is a control signal; fan-out turns branchy *measurement* into a single round-trip; confidence can be control flow; density of judgements over a corpus is the new budget.

**Wrong cost model.** An `if` is ~1 ns. Jev is 70–500 ms and a network hop. It is **not** a hot-loop predicate. It is **not** 60 fps. It *is* economically an `if` (`$0.042 / 1M` input tokens, output free: a 2k-token state is ~`8e-8` dollars). Honest systems analogy: **a Redis/DB round-trip that speaks English and returns a measure.** Put it in a 5–10 Hz controller, a request path, or a map over shards. Do not put it inside a sort comparator.

**Wrong type.** “Judgement costs what an if costs” still sounds Boolean. The whole point is that you received `Δ(τ)`. Using it as a bool is leaving the instruction on the table.

**Wrong claim about fan-out.** Speculative fan-out does **not** evaluate a decision tree. It evaluates **all node questions with no path dependence**. Later questions do not see earlier answers unless you write them back into `state` and call again. What became free is **data-parallel predication**, the compiler transform that turns control flow into a mask. What did *not* become free is sequential reasoning.

**Wrong claim about a “dense field.”** You get a bag of calibrated marginals. Jaggedness §8: negations need not sum to one. Thousands of questions on a bloated state also hit context rot (§5). It is a dense **telemetry bitmap**, not a coherent world model.

**Most correct part of your framing, and the one people will underuse:** Score as a continuous interpolant. That is not a label. It is a **posterior mean on a user-defined ordinal chart** — a semantic sensor. Classifiers do not give you that. Embeddings do not give you an axis whose name you can edit in English.

---

## What follows from the name

If `PMatch` is O(1) round-trips in the number of predicates and returns a probability, these algorithms change class. (O(1) here means **amortized latency in `n` questions**, not RAM-model O(1).)

**Indexes.** Bitmap index, but cells are `p ∈ [0,1]`. A **calibrated property index**: columns are English Nouls/Scores, rows are documents/events, queries are range scans (`hostility ∈ [1.4, 2.1]`). k-d / R-trees in a basis *you named*. Heaps keyed on Score. Materialized views over streams, refreshed at tick rate.

**Feature maps, not formulas.** `φ(s) = (p_1,…,p_n)` is an explicit embedding into a space whose axes have names. Classical models supply the copula: logistic regression / a tiny net learns `P(escalate | φ(s))`. Do **not** compute `P(A ∧ B)` by multiplying Nouls and calling it probability.

**Predication.** Agent programs become: one probe of every guard on the frontier, then a deterministic state machine. That is the same rewrite compilers use to kill branches on a GPU.

**Change detection.** RLCD’s “similar inputs → similar answers” makes `φ(s)` a **semantic fingerprint**. `||φ_t − φ_{t−1}||` is meaning-delta. Cache keys, dedup, dirty bits, hierarchical recompute (re-probe only changed subtrees).

**Control.** Score is a potential. Finite differences across time are a derivative (“this thread is heating”). Choice is an 8 Hz discrete policy head (their Doom number: 0.114 s). Noul is a halt/go sensor. Calibrated `p` makes **naive expected utility** `∑ p_i u_i` less of a lie than LLM logprobs.

**Anytime / confidence-directed search.** Process until entropy is low; escalate when max `p` is near-uniform; skip the frontier LLM when Jev’s entropy is already small (selective prediction). Thompson sampling can consume the returned distribution directly **in-domain**.

**What does *not* become possible:** probabilistic SAT on the Nouls, admissible A* heuristics, temporal window checks, counting, multi-hop properties-of-properties. Those need structure Jev does not return.

The algorithm class in one line: **classical data structures and control loops, in a basis of English finite types, with joints and arithmetic outside the model.**

---

## B. The non-obvious capability

Not “faster tickets.”

**Jev is a compiler target for semantic predication, and a featurizer into a named calibrated basis. The product is the vector `φ(s)`, not the argmax.**

The thing that did not exist last week: you can **lower an English-guarded state machine to a single SIMD probe + deterministic reduce**, and you can **run every classical algorithm that needs a cheap inner product with meaning in coordinates a human can edit.**

Consequences that are easy to miss because the model is four days old:

1. **Independence is the feature.** Do not mourn the missing joint. The right architecture is Jev as lift, a 20-line model or a Pydantic machine as copula. That is how naive Bayes always worked; the new part is that the features are English and 100 ms for the whole vector.

2. **Score is a chart, not a class.** Define 8–64 ordinal axes in prose. Every object becomes a point in `R^k` with *legends*. Cluster, route, and control in that space. Change an axis description, the geometry moves. Embeddings cannot do this: their axes are unnamed. An LLM cannot re-project a corpus on a stage beat.

3. **`φ(s)` is a hash with a training invariant.** Use it as a fingerprint, a cache key for expensive LLM work, a dirty bit, a time series. A “semantic Merkle tree” is just hierarchical Nouls with recompute on change.

4. **Speculative execution of *tools and UI*, not tokens.** Prefetch the two likely next screens, bind the two likely tools, open the likely span in the debugger — from one probe of 40 Nouls you will mostly throw away. That is what “output tokens free / extra questions free” is *for*.

5. **Decision theory without a fudge factor, in-domain.** RLCD is the actual gift. A controller that does `E[u] = ∑ p u` and a halt rule `if max p < τ then human` is now an honest architecture, not a slide. Off the jaggedness list it is theatre.

6. **Closed-world is the type system.** If you cannot name the alternatives before the call, you are holding the wrong instruction. Open extraction, summaries, plans, IDs, dates — those are generation. Jev cannot inhabit `String`.

---

## C. Three ideas that are only possible because of this instruction

Each one is a 3-minute live demo, 8.5 hours, no generation, no math, no dates, no injection-robustness claims. Judges: DeepMind (new class), Conduct (ops), Modal (map), Pydantic (types).

### 1. Branchless intake — predication as the product

**What.** A visible Pydantic state machine for a closed-world intake (bug routing, KYC-lite, insurance first notice — pick one ontology you can write on a card). Every guard on every node is Choice/Score/Noul. One `system_one` call fills the entire tree. Python steps at most one path. Unused branches stay on screen with their probabilities.

**Why Jev.** An LLM tree is serial, seconds per hop, untyped, uncalibrated. Mini-model structured output still costs a round-trip per hop and still parses. Here, **adding the off-path questions does not add latency**, and a type error cannot occur. The demo *is* speculative fan-out. LLM version cannot repaint a 25-node tree in a stage pause.

**Live demo.** Left: a JSON case you edit in one field. Center: the tree, taken edges bright, others dim, each node labelled with `p` and confidence. Right: a single typed `Action` record (approve / ask-one-question / escalate) that is **not allowed to render** unless `confidence` clears a slider. You change “billing” to “the app ate my payment and now I’m posting on Trustpilot.” The tree relights in ~100 ms. The escalate button arms on Noul, not on vibes. Logfire shows one span, 25 answers, zero output tokens.

**Do not** encode “unless,” nested conditions, or “next step *given* the department” as parallel questions. Put facts in `state`; put joints in the machine.

### 2. Editable-basis projector — Score as `R^k`

**What.** A corpus of ~40 real short documents (reviews, emails, HN comments — preloaded, plus a paste box). Eight Score axes, defaulted to things like hostility, confusion, purchase-intent, legal-risk *tone* (not legal conclusion). Each doc is a particle at `(E[axis_i], E[axis_j])`. Axis definitions are editable strings.

**Why Jev.** The float interpolant *is* a coordinate. Fan-out: 40 docs × 8 axes in a handful of calls (Modal map if you want that judge to smile), ~100 ms per call. Re-embed-by-editing-English is not a property of BERT, not of OpenAI embeddings, and not of an LLM you cannot afford to run 320 times on stage.

**Live demo.** Particles on a 2D plane. You ask the room for an axis. You type it. The cloud **slides**. Click a point: full simplex per axis, not just the mean. Drag the “use this as a control signal” slider on one Score; particles above the line go into a live queue. One sentence: “this is an embedding space whose basis is a Pydantic schema.” DeepMind gets the primitive; Pydantic gets the schema; Modal gets the map.

**Do not** ask an axis that is a count, a date order, or “not about pricing.” Literal, unary, ordered sensory axes only.

### 3. 8 Hz semantic controller — the Doom implication, not a ticket inbox

**What.** A fake ops surface: 20–30 work items as sprites in lanes (intake / doing / human / done). **Every tick (~8–10 Hz, matching 0.114 s), one probe** (or one per entity if you must; better: one state blob with a named array, or a tight batch) containing, per item: Choice(lane), Score(temperature), Noul(needs_human). Deterministic physics: Score is velocity toward the human lane; Choice is a force into a bin; Noul above τ is a hard clamp. You never generate a reply. You **steer**.

**Why Jev.** This is a control loop. GPT-class 3–8 s/tick is not a demo, it is a slideshow. Classifiers do not give you a calibrated analog stick. Extra per-entity questions are free, so you pack instrumentation you will mostly discard (Speculative Fan-out as telemetry). Last week this class of UI did not exist without a custom trained head.

**Live demo.** The board is already breathing when you walk on stage (replay a canned stream). You paste one ugly paragraph into “new item.” It appears, heats, and is forced into `human` while a confidence sparkline stays honest. You paste a bland status update; it drifts to `done` slowly. No chat. No summary. Conduct sees an operating system sensor plane; DeepMind sees a policy head; Pydantic sees `Lane | Temperature | Halt`.

**Do not** simulate calendars, SLAs, or “how many times they wrote PLEASE.” Do not play Doom — TypeSafe already did, and you will look like a cover band.

---

## D. The trap

**The seductive misuse is treating `PMatch` as a small LLM, or as a bool.**

You will watch teams:

- Ask it to extract order IDs, emails, dates, next actions as text. **It cannot inhabit `String`.** Closed set or you are wrong.
- `argmax` Choice and ship a 2019 classifier with a $40M story. Judges will say “why not DistilBERT.”
- Multiply Nouls and report `P(A and B)`. Product of marginals ≠ joint. Jaggedness §8 is the warning label.
- Fan-out sequential thought (“if billing, then…”) without writing the premise into `state`. That is not predication, that is a bug with extra questions.
- Put Jev in a 1 ms loop or a 60 fps game. 100 ms is 6 frames. Batch or miss.
- Prompt it like ChatGPT: long instructions in `state` that fight `criteria` (§7), scoping words, double negatives, implied “except” (§1, §4).
- Dump a whole Slack export as one state (§5). Context rot on stage looks like stupidity.
- Use 0.99 as 99% on math, hex, counts, durations, “which date is sooner” (§2, §3). That is how you get a DeepMind judge to destroy you in one question.
- Demo injection resistance (§6). There is none.
- Bolt on an LLM to “make it a product.” Latency thesis dies; you are now everyone else.
- Compete on intelligence vs GPT. The Register is right: not a fair comparison. Win on **density × latency × layout × calibration in a closed world.** Lose on MMLU.

**Demos that will embarrass:**

Anything that needs a number, a clock, a count of entities, a colour code, a translation, a summary, a generated reply, a mixed-intent “both billing *and* crash unless it’s a VIP,” a jailbreak, or an open-set slot fill. Also the obvious ticket classifier: it is true and it is boring, and it reads as “we wrapped a softmax.”

**The type-theoretic failure mode:** using Jev where the answer type is infinite. **The probability-theoretic failure mode:** using marginals as a world model. **The systems failure mode:** calling 100 ms an `if`. **The product failure mode:** generating text.

If the demo still works when you only display `φ(s)` as numbers and never emit a sentence, you understood the instruction. If you need a paragraph out of the model, you brought last week’s object.
