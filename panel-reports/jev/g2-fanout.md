**The load-bearing fact is not 100ms. It is that width is free.** Latency is a rounding error. The new invariant is: the marginal cost of one more semantic predicate, including one you will throw away, is zero. That inverts how you write control flow.

---

## A. Mental model

**Jev is a superscalar decoder for meaning.** One state is the instruction. Each `Choice` / `Score` / `Noul` is an independent execution port. One forward pass fills every port. Your code is the reorder buffer: it commits some answers into program state and discards the rest. TypeSafe already named this Speculative Fan-out. Take the name literally. It is CPU speculative execution, except you take every branch, and discard is free.

The GPU rhyme is even tighter. An LLM is a CPU for thought: deep, sequential, each step waits on the last. Jev is a GPU for judgement: one dispatch, many independent kernels, occupancy is the whole game. Under-asking is leaving ALUs idle. The correct engineering culture is the opposite of prompt-engineering's "be concise." **Always ask everything.**

What it is **not**:

- **Not a fast LLM.** It does not generate, does not chain, does not "think." Calling it a small GPT with a JSON mode is a category error.
- **Not sklearn.** A classifier maps into a fixed label set you trained. Jev maps open-ended state into a schema you declared *this request*. The criteria strings are the program.
- **Not a reasoner.** Questions are evaluated independently, against the same state, with no information flowing from Q1 into Q2. There is no hidden scratchpad.
- **Not a world model.** Jaggedness #8 is the tell: negations are not guaranteed to sum to one. You did not get a coherent joint distribution. You got a bag of calibrated margins.
- **Not an if-statement.** 70–500ms is a network RTT, not a branch. You cannot drop it into a 16ms tick. You *can* drop it into any loop that already tolerated a cache miss to a remote service.

**The class of problem that just became tractable** is any system whose bottleneck was *sequential semantic branching*: you had to know Q1 before you could afford to ask Q2. That family — decision trees over language, policy engines over documents, tool selection over agent state — collapses into "compile the tree into a predicate vector, evaluate the vector, mux in code."

Where your framing is lazy:

1. **"Judgement now costs what an if-statement costs."** Wrong axis, and oversold. The new thing is not that one judgement is cheap. It is that the *Nth* judgement is free. Speed lets you put one Noul in a hot loop. Fan-out lets you put a *surface* in a hot loop.
2. **"A dense field of thousands of judgements over a corpus."** That is N *states*, not N *questions*. The API is one state per request. Fan-out does not classify 10,000 tickets in one call. Packing them into one state walks straight into jaggedness #5 (context rot). Corpus-scale density is a throughput argument. Fan-out is an intra-request width argument. Do not conflate them.
3. **"Evaluate an entire decision tree in one round trip."** Only after you *flatten* it. Every node must be a predicate over the original state, not over previous answers. If Q2 needs Q1's *value* as input — not just as a gate — you cannot fan that out. You either Cartesian-expand into a joint question, or you take a second call. People will say "tree" and ship a chain.
4. **Score-as-control-signal is orthogonal.** A single calibrated float as a PID input is a Score property. Fan-out's version is a *field*: a vector of scores, evaluated together, used as a control surface. Don't steal Score's thunder and call it width.

The sentence that should replace "fast classifier":

**Policy surface area just decoupled from runtime.** Adding a rule used to add a round trip or a prompt collision. Adding a rule now adds a question. Latency stays flat. The incentive flips from under-specifying policy (because every check was an argument against itself) to over-asking (because unused ports are free, and unused answers are information). Judgement becomes like logging after I/O got cheap: you used to sample; now you instrument everything.

---

## B. The non-obvious capability

**The discarded branches are the product.**

Everyone will treat Speculative Fan-out as an optimization: compute extra stuff, throw it away, save RTTs. That is how branch predictors work in a CPU, and it is the small idea. The large idea is that **early commitment was the bug**. Sequential agents are depth-first search with irrevocable commits. They pick "refund," and they never evaluate "structuring fraud." Jev cannot fail to look. Every tick, the entire action surface, the entire policy ROM, and the entire "this would be a mistake if…" taxonomy get values. The path you take is one slice. The paths you didn't take are a shadow consistency channel.

Push that as far as it goes.

**1. Flatten, don't traverse.**
A 3-level tree with branching factor 4 is not 1+4+16 dependent calls. It is ~21 independent predicates on the original state, plus Python that reconstructs which path fired. The technique is Cartesian expansion of dependent decisions into independent joints:

- Bad: Q1 department, then Q2|billing sub-issue. Q2 never sees Q1.
- Speculative: ask Q1, Q2_billing, Q2_tech, Q2_legal against the same ticket. Gate on Q1 in code. Ignore the rest.
- Joint: one `Choice` over the leaves `{billing/refund, billing/chargeback, tech/outage, …}`.
- Overlapping: a Noul per cell of the taxonomy, so a ticket can be *both* billing *and* a legal threat. This last one is strictly more than a single `Choice`. Choice is a simplex (pick one). Noul-fan-out is a covering. Overlapping hypotheses are the thing a classifier-with-argmax hides.

**2. The unit of design is a surface, not a path.**
At the limit, an agent's entire tool mask, entire compliance policy, entire tone guide, and entire user-intent lattice become one instruction word, evaluated every tick. Python ANDs, ORs, thresholds, and muxes. The "program" is boolean algebra over a register file Jev filled in one clock. That is a **semantic CPU**. The ISA is `{Choice, Score, Noul}`. The ROM is your compiled SOP. The clock is a Jev call. Occupancy — how full you packed the question slots — is the performance metric that matters, not tokens/sec.

**3. Unused answers are an ensemble you didn't have to train.**
If the taken path is "simple refund" at 0.93 and the unused branch "sanctions-adjacent" is 0.31, that is the interesting event. A greedy LLM would never have asked. You now get contradiction-as-a-feature: independence means answers *can* disagree, and disagreement is a halt condition. Do not try to make them a coherent Bayes net (jaggedness #8 will embarrass you). Treat them as calibrated margins and look at the residuals.

**4. Evaluate all possible next actions instead of choosing one.**
Today's agent loop: sample one tool, call it, observe, repeat. Tomorrow's: Noul/Score every tool against current state in one call; execute the mask (`noul > τ`) in parallel; hold the mid-band for a human; suppress the rest. Selection becomes covering. This is where Modal stops being a host and becomes the second fan-out — compute fan-out sitting on top of question fan-out. Jev decides *which worlds are worth running*. Modal runs them.

**5. The scaling law that matters is predicates-per-dispatch.**
Once width is free, systems accrete judgement the way they accreted observability. Legal adds 40 Nouls this quarter; runtime does not move. Product adds 15 speculative "might need later" Scores; runtime does not move. The architecture that wins is the one that **keeps the question budget full**, because a question you didn't ask is a world you cannot see. That is not "classify tickets faster." That is a new control plane: whole-program semantic evaluation, once per event, constant time in the number of rules.

**The strongest concrete application:** a **shadow-path auditor** sitting in front of any irreversible act — send, refund, merge, file, delete, promise.

Not "should we send this email?" (one Noul, a classifier). Instead: one call that evaluates (a) every precondition of the intended act, (b) attractiveness of every alternative act, (c) every policy in the ROM, (d) every "this is a mistake if…" condition. Display the taken path and the unused branches that still lit up. Halt if a discarded path exceeds a threshold the taken path did not see. That product was impossible last week because an LLM either committed early (never evaluated the shadow) or evaluated the shadow sequentially (too slow to put on the send button, too expensive to run on every draft, too untyped to wire into a halt).

The thing four-day-old-model people will miss: **fan-out is not a faster search. It is a prohibition on not looking.**

Hard limit, so you don't overclaim: this is breadth over *questions about one state*, not breadth over *states*. You cannot score 50 hypothetical next worlds in one call unless you pack them, and packing is context rot. You also cannot do multi-hop inside the dispatch. Jev fills registers. It does not reduce a graph. If the next predicate needs a fact that is not in the original state, you are back to a second call or you are lying to yourself about flattening.

---

## C. Three hackathon ideas (fan-out or nothing)

Constraint I am designing to: 8.5 hours, 3-minute stage demo, judges who each need a sentence. DeepMind needs a new inference shape. Conduct needs an OS tick. Modal needs real parallel work, not a billed hello-world. Pydantic needs a schema that *is* the product, traced in Logfire. None of these is "we classified the ticket in 90ms."

### 1. SHADOWWORD — the branches you didn't take are the halt condition

**What.** A send/refund/merge console. Paste the artifact (email, refund rationale, PR body). One `system_one` call with ~60–80 questions: intended-act preconditions, every alternative act as a Score, every policy as a Noul, every "implicit commitment / wrong recipient / sanctions-adjacent / promises money we didn't approve" as a Noul. The UI is a path: green spine for the act you asked about, amber ghosts for unused branches that still fired. One ghost over threshold blocks the act.

**Why Jev, specifically the width.** An LLM demo either asks one "is this OK?" (misses the ghost) or chains 80 checks (you will time out on stage, and it will drop fields). Schema-guaranteed answers mean the halt predicate is Python, not a vibes parse. Confidence is the discard gate: you *show* the unused branches, you do not *trust* them unless the branch predicate also fired. That is the whole product, and it only exists if 80 questions cost the same as 1.

**Live demo (3 min).** 0:00 paste a clean refund email, green path, send stays live. 0:40 paste a near-identical email that quietly promises a free month. Taken path still looks like "polite billing reply." A discarded-branch Noul — `implicit_unapproved_credit` — spikes. Send freezes. 1:20 flip Logfire: one span, 80 typed answers, the halt is a threshold on a field. 2:00 one sentence to Conduct: this is an OS interrupt, not a chatbot. 2:20 one sentence to DeepMind: non-autoregressive evaluation of a policy surface; greedy decode would never have asked. Do not generate the email on stage. Preload two artifacts. Do not let Jev do math on the refund amount.

### 2. FULLMASK — do not pick the next action; evaluate the covering and run it

**What.** An incident comes in as state (alert + last 20 log lines as named JSON fields). You do **not** choose a runbook. You Noul every runbook and every tool (~25–40). Answers become a bitmask. Every bit above τ launches a Modal sandbox (restart probe, config diff, dependency health, similar-incident search). The screen is the mask lighting up, then four sandboxes racing, then a merge of what came back. Jev never writes a word. Python types the mask with Pydantic. Modal is the second fan-out.

**Why Jev, specifically the width.** Speed alone would let you pick the *best* runbook fast. That is still greedy decode. Width lets you refuse to pick. The product is "run every world that is plausible," which is a different object than "classify the incident." An LLM tool-caller emits one function name. You cannot demo four parallel runbooks from one completion without lying, waiting, or breaking the schema. Question-fan-out produces the mask in one RTT; compute-fan-out spends it.

**Live demo.** 0:00 paste a messy incident. 0:08 the 30-cell mask fills (this is the wow; rehearse that it is *one* round trip, put the RTT on screen). 0:10 four cells go hot, four Modal functions spawn, four panes fill. 1:20 show a cell that was *almost* hot and was correctly left dark — covering, not argmax. 2:00 Logfire: `Mask` model, each bit a span. 2:30 Conduct sentence: the OS computed an action covering, not a chat plan. Seed the incident. Do not scrape live prod. Pre-warm Modal. If Modal hiccups, the mask UI still wins the room; the sandboxes are the sponsor beat, not the existence proof.

### 3. POLICYROM — the program is a question set; the CPU is one call per event

**What.** A one-page SOP (refunds, data-retention, "can this support agent promise X") compiled *once* before the demo — by you, by hand, into a frozen dict of `Choice`/`Score`/`Noul`. That dict *is* the program. Then a firehose of incoming events (tickets, Slack-shaped commitments, draft replies) each gets the **entire ROM** evaluated in one call. The UI is a ROM dump: every rule a cell, cells light at 10Hz as you paste or replay. Adding a rule at the end of the demo is adding one question; you make a point of the latency not moving.

**Why Jev, specifically the width.** This is the "marginal cost of a rule is zero" demo. An LLM-based policy engine either stuffs 80 rules into a prompt (jagged, untyped, slow) or calls once per rule (unusable live). Jev is the only thing that lets you put a 60-rule program on a per-event tick and still have a stage demo. Pydantic: the ROM is a typed schema. Conduct: this is an AI operating system in the literal sense — a fetch-decode-execute loop where decode is semantic and execute is Python. DeepMind: the "weights" of the policy are criteria strings, the inference is non-autoregressive, the control flow is outside the model. That is a new split.

**Live demo.** 0:00 show the SOP and the frozen question dict side by side — compilation already done, do not LLM-compile on stage. 0:20 replay five events; the same ROM lights differently; one event lights two overlapping Nouls (legal + billing) that a single Choice would have collapsed. 1:20 *add a rule live* ("never promise a credit above the user's plan") as one Noul; replay the same event; latency number on screen does not move; the new cell is the only thing that changed. 2:10 Logfire of the tick. 2:30 "policy surface decoupled from runtime." Hard-code the ROM. If you generate questions live you will eat the clock and ship contradictions into criteria (jaggedness #7).

**Cut order if the morning goes badly:** SHADOWWORD first (one call, two artifacts, halt is visible). FULLMASK second (Modal is extra moving parts). POLICYROM only if someone on the team is fast at UI grids. All three share one SDK-shaped core: `state` in, big `questions` dict, Python mux. That is an 8.5-hour object. Generating text is not.

---

## D. The trap

**The seductive-but-wrong use is treating fan-out as sequential reasoning with the round trips deleted.**

You will see it on stage as: "we evaluate the whole tree." What they shipped is Q2 whose criteria *assume Q1's answer*. Jev never saw Q1. Questions are independent. That is why width is free — and why this is not a reasoner. The unused-branch questions whose criteria contradict the state are not "probably low confidence." Jaggedness #7 says contradictory instructions vs criteria *degrade badly*. Speculative questions are not free of semantic cost just because they are free of latency cost. If you display or trust an unused branch without gating on the branch predicate, you will demo garbage and call it a shadow path.

Where people will misuse it, in order of how fast it dies on stage:

1. **Fake multi-hop.** "First extract the date window, then test whether the claim falls in it." Jev reads dates as text (jaggedness #3) and cannot feed Q1 into Q2. Any demo that needs properties-of-properties, double negatives, or "given that…" inside one call is already dead (jaggedness #4). Flatten or take the second RTT. Do not pretend.

2. **Cartesian pollution.** Asking `billing_subissue` on a clearly-technical ticket, with criteria written as if billing were true. You thought you were being speculative. You handed the model contradictory instructions. The right speculative form is criteria that remain well-posed on *every* state ("if this is not billing, pick `not_applicable`") plus a code gate. Missing `not_applicable` is how a clever fan-out demo embarrasses itself.

3. **Coherent probability theater.** Summing Nouls, treating Choice option probs as a simplex, doing Bayes over the question bag, drawing a pretty calibrated-reliability diagram you did not earn. Jaggedness #8: no structural invariants. DeepMind will notice. Use margins, thresholds, residuals. Do not build a world model out of independent ports.

4. **Packing a corpus into one state.** "Dense annotation of the graph at once." That is N states. One fat state with distractors is jaggedness #5. The demo that pastes an entire thread plus six PDFs plus a taxonomy of 200 questions will context-rot in front of Pydantic.

5. **Argmax cosplay.** Taking `Choice` and displaying only `.choice`. You paid for a distribution and a confidence and then threw away the product. The interesting bit is the second mass and the unused Noul. If your UI is a single label, you built last week's classifier with a new logo.

6. **Generation-shaped demos.** Live email writer, live runbook author, live SOP compiler. Jev is not trained to generate text. If the wow requires a paragraph, you now have an LLM in the loop, and you are back to last week's latency, cost, and schema risk, with Jev as garnish. Compile offline. Template the words. Let Jev fill registers.

7. **Math, counts, hex, durations, "within 14 days," "three mentions of refund."** Jaggedness #2 and #3. A judge will ask "how many?" and you will die. Put numbers in code. Put meaning in Jev.

8. **Adversarial / prompt-injection "safety" demos.** No default defence (jaggedness #6). Do not claim the shadow auditor is an injection shield. It is a policy-surface evaluator. Those are different.

9. **Literal scoping.** "Except for VIPs," "unless already refunded," "not counting internal threads." Jaggedness #1. Criteria must be written like code comments for a hostile intern: no implied conditions. If your ROM is full of lawyer-English, POLICYROM will light the wrong cells and you will not know until the Q&A.

**The embarrassment signature:** a heatmap of 80 questions that *looks* like whole-program evaluation, followed by a judge picking one cell that is a negation, a date, or a dependent clause, and watching it be confidently wrong. Width makes that more likely, not less, because you asked more things. Fan-out without gating, without `not_applicable`, without keeping criteria well-posed on every state, is how you turn the actual unlock into a larger attack surface for jaggedness.

Design rule for tomorrow morning: **every speculative question must be a legal question about the raw state, including the worlds where it "shouldn't" fire.** The discard happens in Python. If you need the discard to happen in the model, you are not doing fan-out. You are doing a chain and hoping no one counts the RTTs.
