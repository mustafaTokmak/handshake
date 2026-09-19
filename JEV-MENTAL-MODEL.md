# Jev / System One — mental model, and what it changes for the hackathon

11-model panel (5× Grok as requested, 2× Codex, Kimi K3, DeepSeek v4.1, Opus, Sonnet).
Raw reports: `…/scratchpad/jev/`. Sources: [TypeSafe blog](https://typesafe.ai/blog/introducing-system-one-models-and-jev) · [docs](https://docs.typesafe.ai/) · [OpenRouter](https://openrouter.ai/typesafe) · [InfoWorld](https://www.infoworld.com/article/4223468/typesafe-ais-new-models-work-with-machines-not-humans.html) · [The Register](https://www.theregister.com/ai-and-ml/2026/09/16/typesafe-ai-debuts-model-for-machines-that-plays-doom/5296711)

---

## 1. The one-line model

```
PROBE : State × (Name ⇀ FiniteType) → ∏ᵢ Δ(τᵢ)
```

**You declare the types first. One forward pass inhabits all of them. Extra coordinates are free. You get back a product of marginals — not a joint.**

That last clause is the whole mental model. Almost every documented weakness falls out of it:

| Primitive | Type | What comes back | Honest reading |
|---|---|---|---|
| `Choice` | finite set | categorical + `confidence` | a **named simplex** |
| `Score` | ordered levels | float + per-level probs + `confidence` | **a probability-weighted mean of the level *numbers*** — see the warning below |
| `Noul` | binary | `p ∈ [0,1]`, **no confidence field** | a **Bernoulli parameter** |

Because questions are evaluated **independently against the same state**, you did not get a Bayesian network, a coherent world model, or `P(A ∧ B)`. You got a named feature map `φ(s) ∈ [0,1]ⁿ` whose coordinates are *separately* calibrated. Hence: negations need not sum to one, no multi-hop, no cross-question consistency. Those aren't bugs; they're the type signature.

### ⚠ The Score float is uncertainty, not intensity

The single most misleading thing about this API, straight from the docs: *"The score is a probability-weighted mean of the level numbers… 0 × 0.0 + 1 × 0.70 + 2 × 0.30 = 1.30."*

So `frustration = 1.035` does **not** mean "slightly above level 1 in intensity." It means **96.5% on level 1, 3.5% on level 2**. The continuity is manufactured out of the model's uncertainty — the smoothness of the signal *is* the spread of the distribution.

The point estimate is also degenerate — `p = [0.5, 0, 0.5]` and `p = [0, 1, 0]` both yield 1.0 and mean opposite things. Read the `probabilities` map, not just the float.

**But "it's only uncertainty" is half right.** Score is an *ordinal latent-variable readout*: a **monotone but non-linear** function of true intensity, contaminated by epistemic spread. So:

- **Sound (monotone) uses:** rank, threshold, direction-of-change, "is A worse than B."
- **Unsound (metric) uses:** differences, averages, PID gains, anything treating 1.0→2.0 as equal to 2.0→3.0.

**The adjacency test** separates real interpolation from ignorance, and it beats gating on `confidence` (which conflates the two): mass concentrated on **two adjacent levels totalling ≥0.90** is genuine interpolation — trust the float. Anything more spread out is the model not knowing, and the float is an artifact.

**More levels do not buy resolution.** You already have infinite resolution via the expectation; going from 3 levels to 7 buys *linearity and anchoring*, and mostly converts crisp adjacent-pair spread into mush. **For a genuinely clean semantic magnitude, use a ladder of monotone threshold Nouls instead of one Score** — "is it at least X?" at ascending X. Free under fan-out, gives you the entire CDF rather than one moment, and any non-monotonicity in the ladder is a free rubric-validity detector.

### The stability clause is the quiet headline

RLCD's second objective — *"similar answers for similar inputs"* — makes this plausibly **the first model explicitly trained to be approximately Lipschitz-continuous in its input.** An LLM judge can flip class on a whitespace change; Jev is optimised not to. That smoothness is the licence to put a model inside a feedback loop, a finite-difference computation, or a control law at all. Without it, most of §3 doesn't exist.

**But the guarantee is over *state* variation with criteria held fixed.** Calibration is defined per-question, so it cannot certify a moving rubric — and two jaggedness items are explicitly criteria-side. **Editing criteria redefines the instrument**: it invalidates your thresholds, your calibration curve, any stored semantic column, and any time series spanning the edit. Treat `hash(criteria + model version)` as the **scale identity** and refuse comparisons across it.

Stage consequence, and it's a real one: **never animate a needle across a rubric edit** — that's a dishonest comparison and a DeepMind judge may well say so. Show the *reordering* instead. Better: **edit weights, not criteria.** For Breaker this is good news — the threshold slider (θ) is a weight edit, so the best interactive beat in the demo is also the principled one.

### The analogies that survived scrutiny
- **A GPU for predicates.** Bind state as the texture, declare a framebuffer of finite types, one dispatch, every channel is a calibrated probability. Under-asking is leaving ALUs idle.
- **A semantic sensor / ADC for meaning.** Messy signal in, a few well-typed readings out, cheap enough to leave in the loop. You fuse many readings; you never trust one.
- **A coprocessor for closed questions.** Code owns control flow, arithmetic, time, identity and commits. An LLM owns plans and prose. Jev owns what both are bad at.

### What it is NOT — all five panels agreed
Not an LLM with JSON mode. Not a classifier (the label set is part of the *query*, supplied at inference). Not a reasoner (no scratchpad, nothing to scratch). Not a calculator, clock, or writer. Not a security boundary. **Not an if-statement.**

## 2. Where my framing was wrong

I said "a calibrated semantic judgement now costs what an if-statement costs." Four panels attacked it and they're right:

1. **Off by six-to-eight orders of magnitude.** An `if` is ~1ns and deterministic. Jev is a 70–500ms network RPC. The honest analogy is **a Redis/DB round-trip that speaks English and returns a measure**. It fits an event loop, a request handler, a 5–10Hz controller, a UI typing loop. It does **not** fit a 60fps tick or a sort comparator.
2. **Wrong axis.** The unlock isn't that one judgement is cheap — it's that **the Nth judgement is free**. Speed puts one predicate in a loop; fan-out puts a *surface* in a loop. As Grok-2 put it: *policy surface area just decoupled from runtime.* Adding a rule used to add a round-trip; now it adds a question and latency stays flat.
3. **Fan-out is intra-request width, not corpus density.** One state per request. "Thousands of judgements over a corpus" is a `Modal.map` throughput argument over many small payloads — *not* one fat state, which walks straight into context rot. Conflating these is the most common way to design this wrong.
4. **Fan-out does not evaluate a decision tree.** Questions never see each other's answers. You can only flatten nodes that are predicates over the *original* state. If Q2 needs Q1's value, you either Cartesian-expand into a joint question or pay a second call. **People will say "tree" and ship a chain.**
5. **Schema-safety relocates the failure, it doesn't remove it.** A confidently wrong answer that parses perfectly is *worse* than a type error: type errors throw, semantic errors silently branch your code on a wrong `0.99`. The Register's line is fair — you can't misspell JSON if you never emit JSON. Constrained decoding solves the *decoder*; truth is a *world* constraint. Grok-4: **"a hallucination with a Pydantic badge."**
6. **Calibration is not correctness.** At confidence 0.7 the model is *supposed* to be wrong 30% of the time. And it's calibrated on *their* distribution, not your hackathon data — trust the ranking (A > B) more than the absolute value.
7. **The Score mean can be a state that doesn't exist.** If mass is bimodal (50% level 0, 50% level 2), the mean 1.0 is steering toward the average of two cities. Halt on bimodality; use the distribution, not the expectation. And per the warning in §1, the float moves with *uncertainty*, not intensity — so "Score as a control signal," which I listed as an unlock, is only sound once you read the `probabilities` map alongside it.

### The analogy I'd actually use

**A programmable measuring instrument for meaning, with a published accuracy spec and a published operating envelope.** Every clause does work: it's a transducer (unstructured quantity → number on a scale); *you bring the scale*, so `criteria` are engraved gradations rather than a prompt — **the criteria are the program and the model is the interpreter**, which is why the discipline here is *writing a rubric*, not prompt engineering; every reading ships with its precision, and "of everything marked 0.8, about 80% is right" is an accuracy spec, which is the sharpest break from LLMs; and it has a response time and cost per reading, which set your sampling rate.

Analogies the panel tested and discarded: **classifier** (label set is a runtime argument, and calibration is the objective — it's the thing that makes per-task classifiers unnecessary); **oracle** (oracles are assumed correct and have no error bar; the error bar is the entire value); **semantic ALU** (an ALU is exact, deterministic and *total* — Jev is approximate, stochastic and undefined over a documented chunk of its domain, so anyone reasoning "ALU" writes code that assumes totality and gets bitten by the dates); **JIT for judgement** (nothing is compiled — cute and empty).

## 3. What's genuinely new

Strip the marketing and the defensible claim is narrow but real: **frontier-quality, untrained-per-task, schema-locked, calibrated, non-generative judgement at ~100ms, with free width.** Fast closed-set models existed (BERT, zero-shot NLI, SetFit). What didn't exist as a general API was all of those properties at once, with the criteria written in English at call time.

It's a **unit-economics unlock for semantic features**, not a phase change in intelligence. That's still a big deal, because the economics were the binding constraint.

The two capabilities the panel rated most under-exploited:

**Semantic telemetry.** StatsD gave you `latency_ms` and `error_count`. You could never afford `user_is_about_to_churn` or `this_span_looks_like_a_regression` on every event, because the only general sensor was an LLM. A Noul is a gauge, a Score is a histogrammable float, a Choice is a categorical, fan-out is a scrape, 100ms is a scrape interval. Over-provision gauges the way you over-provision dashboards — don't fix the ontology up front, scrape 40, keep the ones that move.

**Meaning becomes a number that can enter an objective function.** `expected_loss = P(wrong_entity) × account.value`. That's not classification, it's control. It makes calibrated branch-and-bound, information-gain question selection, and hill-climbing against a semantic fitness function actually runnable — DeepSeek's point that the eternal bottleneck of heuristic search was the heuristic, and it's now a runtime English rubric.

**The design rule that follows:** put Jev in the **observability plane**, and only let it reach the control plane through thresholds, hysteresis, escalation and rollback. Wrong 15% of the time as a metric is a noisy probe; wrong 15% of the time as an `if` is an incident.

## 4. What this means for the hackathon

### Jev resolves the deadlock from round 2

Round 2 split 4–3–1. Three agents wanted to move the intervention **before** the write (PRECHECK / Airlock / SHADOW). The judge simulation killed it on two grounds: it files instantly into `terraform plan` / confirm-dialog, and — the sharper one — *"if a human stamps every write, you have deleted the agent."* Approval-queue fatigue is exactly what Conduct's customers already tried and switched off.

**Jev removes that objection.** A calibrated gate doesn't queue everything for a human — it runs autonomously when confident and halts only on the genuinely uncertain call. That was never buildable before, because an LLM gate on 14 serial tool calls is 20–40 seconds of dead air and uncalibrated Booleans. At ~150ms per call it fits in the stream.

### The idea: **Breaker** — a circuit breaker on the tool path

The same overnight wreck as Unwind, but nothing commits. Each proposed write hits one Jev bundle: wrong-entity, irreversible, duplicate-refund, human-already-moved, blast-radius Score, plus the speculative extras you discard. Python owns money, dates, IDs and commits. Gemini only plans, and rewrites on halt.

**The wow is a number, not a table.** Bars flash past at 0.97, 0.94 — then **0.54 same-customer → HALT**. The termination email never leaves. Then the split screen: same state, Gemini Flash returns `is_same_customer: true` in 3.1s. *"We stopped using a language model as a Boolean factory."*

Why this beats Unwind on every axis the earlier panels cared about:
- **It has the fire** (the wreck still happens) but it's first-order — nothing to hold in your head.
- **It isn't a confirm dialog**, so it doesn't file into an existing folder — the thing on screen is a calibrated probability driving autonomous action, and a threshold slider is Conduct's knob made physical.
- **Two big readings, not eleven rows** — already satisfies the judge-sim's highest-leverage fix.
- It keeps the irreversible-email beat, the best credibility moment in the whole plan.
- It kills Unwind's worst problem: the "inverse synthesiser" that three agents showed collapses to `restore(before)`.

### The hard constraints before you commit

- **Access.** The TypeSafe console is **waitlist-gated**. OpenRouter is the only realistic same-day path: `typesafe/jev-1.13` (alias `~typesafe/jev-latest`), base `https://openrouter.ai/api/v1`. **Verify a working key before Saturday** — this is the single go/no-go.
- **32K context**, which matters given documented context rot. Small, named, curated state.
- **`Noul` has no confidence field.** Do not design a confidence gate on Noul — use `Choice` or `Score`.
- **Install the official agent skill** (`docs.typesafe.ai/agent-skill.md`) — it drops into Claude Code and saves re-deriving the API. `pip install typesafe-sdk` (0.7.0, updated 2026-09-18).
- **No sponsor support.** TypeSafe isn't a sponsor — no booth engineer to unbreak you, no priority quota. Kimi's read: no goodwill bonus, but no penalty either; these four judges respect someone who found a frontier artifact four days after launch and used it *competently*.
- **Jev reportedly does worse on invoice-processing-style tasks specifically**, and trails top comparators on aggregate workflow scores. That is uncomfortably close to Breaker's domain — test the actual judgements in hour one.
- **Don't cite 40–200×.** Those are TypeSafe's own evals scored by *agreement with other models*, not ground truth. If you need a defensible number, cite the independent Every.to test: ~25× faster, ~580× cheaper, and it missed one defect out of seven. Saying that out loud makes you the credible team.

### The traps, from the jaggedness list

Do not, on stage: count or tally anything; mention dates, durations or windows (it reads dates as text); chain multi-hop questions; treat "not urgent" as the complement of urgent (no structural invariants); feed it long states with distractors; let audience-supplied text steer a judgement (**zero injection defence**); ask it to write anything.

Three framing traps:
1. **Building an agent out of it.** It can't generate, plan, or hold state. If your architecture has Jev deciding what to do next, a DeepMind judge says so in the first thirty seconds. The correct inversion: the LLM is the slow outer loop that builds the structure; Jev is the fast inner loop that evaluates it.
2. **Betting the wow on one call.** Design so no single judgement can sink you — aggregate demos (a curve, an index, a field) have statistical insurance. Breaker's mitigation is that the halt is *seeded*: you know which call returns 0.54 because you chose the fixture.
3. **Pitching the model instead of the system.** *"We used Jev!"* is the graveyard. *"Judgement just became cheap enough to put on the hot path — here's what that world looks like"* is the win, with Jev named once, as a fact.

**And the demo rule that follows from RLCD:** if you don't show a ~0.5 that you *refuse to trust*, you haven't demoed Jev — you've demoed softmax theatre. The honest uncertainty is the product.
