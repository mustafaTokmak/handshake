[0m
> build · deepseek-v4.1-flash
[0m
## A. The mental model

**The one line:** Jev is a *typed oracle*: `Judge(State, Question) → Distribution[T]`, priced `O(1)` per question and `O(states)` in total. Semantics now has a type and a cost model. Everything interesting follows from those two facts, not from the 100ms.

**Sharpest defensible analogy:** a **SIMD ALU for meaning**. The parallel sampler is literally a wide lane; each lane is an independent typed judgement; `state` is the operand, `questions` are the opcode. Compare to the alternatives and they fail: "classifier" returns a fixed label for a fixed task, whereas Jev answers an *arbitrary, runtime-specified* question — that's the difference between a model and an instruction. "Accelerated LLM" fails because there is no generation, no multi-hop, no arithmetic.

The right formal frame is the **oracle model of computation**. What matters is not wall-clock, it's *oracle complexity* — how many distinct queries your algorithm makes, and what it can ask. And the cost function is unusual: **questions per state are nearly free, states are not.** So the winning algorithms ask *many* questions about *few* states. That is the exact opposite of LLM-native design (short prompts, minimal retries).

**Where your framing is lazy** (the three corrections that matter):
1. "Costs what an if-statement costs" understates it. An if-statement carries no error model. Jev returns a *calibrated probability*, which is what makes optimization and pruning *sound*. The type, not the speed, is the unlock.
2. Speed alone would just be "faster classifier." The real shift is the cost inversion: budget in **states touched**, not calls made. Design discipline becomes "materialize the frontier, fan out every question you might need, branch in code."
3. "Dense field" is right but must be costed: `O(n)` states is fine, `O(n²)` pairwise comparisons is not. Batch it — `state` can be an array, so you assign/bucket many items per call.

**What is NOT tractable, ever, through Jev:** arithmetic, counting, date ordering/durations, multi-hop chains, logical negation as complement, generation. Those stay in your code. This is not a limitation to work around; it is the *division of labor* that makes the thing fast.

**The class of problem that just became tractable:** combinatorial search and decision-making where the objective function is a natural-language string. Yesterday the objective had to be hand-coded, learned from labels, or produced by an LLM too slow and too expensive to sit inside a loop. Today the objective is a runtime string with a calibration score.

## B. The non-obvious capabilities (ranked by mechanism)

1. **Calibration turns a heuristic into a *bound*.** This is the upgrade nobody will exploit. Noul("can this subtree beat the incumbent plan?") returns P(yes); prune when P < ε and you get search with a controllable false-prune rate. Greedy search becomes **calibrated branch-and-bound**. Not possible before because no cheap oracle was calibrated.
2. **Jev's stability property enables semantic transposition tables.** "Similar answers for similar inputs" is exactly the property that makes a Zobrist-style memoized search *sound*. Canonicalize states, cache judgements; revisits in A*/beam become free. This cuts search cost by orders of magnitude and is invisible in every LLM comparison.
3. **A programmable heuristic vector.** Questions-per-state are free, so `h = w₁·Score₁ + w₂·Score₂ + ...` with weights owned by code. The semantics live in Jev; the algebra lives in Python. You can *tune the objective live*, on stage.
4. **Noul is a *queryable family* of metrics, not one fixed metric.** Embeddings give a single isotropic similarity. Noul("are A and B the same *for purpose Y*") gives a task-conditioned metric, and because `state` is an array you get batched assignment — cluster 5k items under a *new English criterion* in seconds.
5. **ID3 with a calibrated oracle.** One fan-out yields P(yes) for *every* candidate predicate; code computes expected information gain and asks the maximizing question. Runtime-built decision trees.
6. **Score is smooth, so gradient-free optimization works.** 1.035 interpolates. Discrete labels give no direction; an ordered continuous score gives hill-climbing/annealing a usable gradient over semantic design space.

**The most powerful of these is heuristic search**, because it is the universal combinatorial optimizer and its eternal bottleneck was the heuristic. Jev makes the heuristic a runtime English rubric, calibration makes it prunable, fan-out makes the frontier parallel, and stability makes revisits free. That is a full algorithm, not a faster classifier.

## C. Three hackathon ideas

### 1. FLAGSHIP — "Referee": semantic A* with calibrated branch-and-bound
**What it is.** A live re-planning engine. A fixed library of actions (rollback, scale, flag-off, drain, page, comms) gets combinatorially instantiated by code into thousands of candidate next-steps. Jev fans out and scores every node against a **rubric vector you type on stage** (restores service / limits blast radius / preserves data integrity / reversible / comms risk). Code computes `g` numerically and `h` from Jev's scores; calibrated Nouls prune subtrees by risk. Beam-3 plies, re-plan every tick. Domain for the demo: an incident war room — it maps directly onto Conduct's buyer, and it generalizes instantly to negotiation and deal-making.

**Why Jev specifically.** The heuristic must be evaluated tens of thousands of times per plan, be *calibrated* so pruning is sound, and be *re-composable* mid-search. GPT-5.6 at 8.5s/generation makes one ply a multi-hour job; even one call per node is impossible. Don't ask Jev to sum costs (it can't) — Jev supplies `h`, code supplies `g`. That split is the whole trick and it's the MuZero-style value/policy separation a DeepMind judge will recognize as correct.

**3-minute live demo.** Type the rubric and drag weights (0:00–0:30). First plan condenses out of a wall of thousands of scored futures (0:30–1:30). Inject a new fact — "the DB is read-only across regions" — and watch the plan rewire in under a second (1:30–2:15). Drag "risk" up; the plan goes conservative and the chosen line shows a calibrated confidence (2:15–2:45). Pull-quote: *"40,000 futures, 900ms, nine hundredths of a cent, and the objective was a sentence I typed thirty seconds ago."*

### 2. "The Interrogator": information-gain diagnosis
**What it is.** An agent that identifies a held-out fault by asking the question that maximally reduces entropy. Each turn, fan out Noul over every candidate question → code computes expected information gain → ask the argmax → update the posterior. It is ID3 built at runtime from an oracle.

**Why Jev.** It needs dozens of *calibrated* probabilities per step at sub-100ms. LLMs are uncalibrated, so their information-gain estimates are garbage (they confidently ask useless questions) — this demo *shows* the LLM baseline losing. 

**3-min demo.** Audience member picks a fault on a card; agent nails it in five questions, entropy bars collapsing live; side-by-side, a GPT baseline flails and mis-ranks its own questions. Ends on "the diagnosis tree did not exist five minutes ago."

### 3. "The Living Map": task-conditioned clustering
**What it is.** A continuously maintained semantic map of a signal stream (tickets, calls, news). Noul is the metric; batched array-state calls assign items to prototypes; Choice re-labels clusters; Score gives a density field.

**Why Jev.** A *field* of judgements under *many* questions, maintained live, with the metric itself re-specified in English. Embeddings cannot do this: their metric is fixed. Watch the same 5,000 items re-sort under a new notion of similarity in one second.

**3-min demo.** Flood 5k items; clusters form; then type "now group by *intent to churn*, not topic" and the entire map re-organizes instantly. The wow is that the *question*, not the data, changed.

## D. The trap

**The seductive wrong thing is "a fast LLM."** People will drop it into an agent loop, prompt it with instructions, ask it to reason, and watch it fail. The correct inversion: **the LLM is the slow outer loop that builds the structure** (action space, rubric, candidate questions); **Jev is the fast inner loop that evaluates the structure.** Jev is a *component*, not an agent. If your architecture has Jev "deciding what to do next" via reasoning, you have built the wrong thing — and a DeepMind judge will say so in the first thirty seconds.

**The second trap: schema-valid ≠ true.** "Never makes type errors" is guaranteed; semantic correctness is not. Every demo that treats a well-formed answer as a correct one is one adversarial input from embarrassment — and adversarial/injected text is *explicitly undefended*.

**What the jaggedness list forbids live:** count or tally anything on stage (code); mention dates, durations, or windows (code — it reads dates as text); chain multi-hop questions (keep single-hop, compose in code); rely on "not urgent" as the complement of urgent (there are no structural invariants; negations don't sum to one — use the probability); feed it long states with distractors (context rot — split the state); let audience-supplied text steer the judgement (injection); ask it to write anything (it cannot).

**The meta-trap: confidence as truth.** Calibration is claimed on *their* distribution; your demo's inputs are not on it. Printing "0.999" and assuming it holds is a coin-flip. Either show a reliability curve proving calibration on your domain, or never lean on the number. Related: a **noisy comparator breaks sorting and bisection** — mitigate with cheap repeated measurement, and never pay `O(n²)` comparisons when a batched array-state call gets you `O(n/k)`.

Net: the winning 8.5-hour build treats Jev as a **typed, calibrated oracle wired into a real algorithm** — search, information gain, or metric construction — with an LLM doing only the slow structural work around it. The losers will build a fast chatbot.
