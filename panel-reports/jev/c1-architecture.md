Reading additional input from stdin...
OpenAI Codex v0.154.0
--------
workdir: /private/tmp/claude-501/-Users-mustafatokmak-st-claude-projects-agentic-ai-hack/afd6cd31-43c8-44cd-8067-b72d90bdba85/scratchpad
model: gpt-5.6-sol
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a0b847-5c23-70c0-8b68-481d05c803de
--------
user
# JEV / SYSTEM ONE — capability brief + idea brief

A genuinely new model class landed on 2026-09-15. I am at an agentic-AI hackathon in London and want to know what it makes possible that was impossible last week. Verified facts only below — all from TypeSafe's own docs, blog, OpenRouter, and press.

## What it is

**TypeSafe AI** emerged from stealth 2026-09-15 with $40M seed. Founded by **Diogo Almeida** (ex-OpenAI, co-inventor of RLHF/ChatGPT), Erik Gafni, Sasha Sheng. First model: **Jev** (current: Jev 1.13).

They call it a **System One Model** — "a new class of frontier models built to make fast, structured decisions that software can use directly."

**It is not an LLM and it does not generate text.** The framing from their blog: *"Think of Jev as a frontier-intelligence function call: unstructured state in, typed probabilistic decisions out."*

### Architecture
- **Non-autoregressive.** No token-by-token generation. A **parallel sampler** produces all outputs in a single forward pass.
- Trained with **RLCD — Reinforcement Learning for Calibrated Decisions**, as opposed to RLHF (human preference) or RLVR (verifiable reward). The optimisation target is *calibration*: "higher confidence means higher accuracy", and "similar answers for similar inputs".
- Output structure is defined in advance, so **schema violations are impossible by construction**, not merely unlikely. TypeSafe: "The model never makes type errors." (Fair caveat from The Register: it "isn't a fair comparison as its output is not natural language.")

### The three primitives (this is the whole API surface)
```python
pip install typesafe-sdk
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
client = TypeSafeClient()   # reads TYPESAFE_API_KEY, defaults to jev-latest

response = client.system_one(
    state="...",                      # str | JSON object | array
    questions={"department": Choice(...), "frustration": Score(...), "is_urgent": Noul(...)},
)
response.answers["department"].choice      # "billing"
response.answers["frustration"].score      # 1.035   <- CONTINUOUS, interpolates the ordered levels
response.answers["is_urgent"].noul         # 0.999   <- probability that the answer is yes
```

- **Choice** — pick one from a closed set. `criteria` is a dict of option -> description. Returns the choice + a probability for every option.
- **Score** — rate against *ordered, described levels*. `criteria` is an ordered list of level descriptions. Returns a **float** that interpolates between levels (e.g. 1.035 on a 3-level scale), plus per-level probabilities.
- **Noul** — a yes/no question that returns **the probability of yes**, not a boolean.

Every answer carries calibrated probabilities and a confidence score.

**State** can be a string, a JSON object (recommended — named fields keep relationships clear), or an array (e.g. a message sequence). One state per request, evaluated against N questions, each evaluated independently.

### The economics — this is the part that changes what is buildable
- **70ms–500ms end-to-end.** (Their Doom demo: Jev 0.114s vs GPT-5.6 Terra 8.566s.)
- **$0.042 per million input tokens. Output tokens free** — "too cheap to meter."
- Claimed 40x–200x faster, up to 190x faster / 440x cheaper than frontier LLMs on their published workflows (their numbers, "on the higher end of real world gains").
- **Adding more questions to a call typically adds no latency.** They name the resulting pattern **Speculative Fan-out**: ask every question you *might* need — including ones only relevant on branches you probably won't take — in one call, and let your code discard the irrelevant answers. Branching that used to cost a round-trip per hop is now free.
- Available on **OpenRouter in beta**: base `https://openrouter.ai/api/v1`, model id `typesafe/jev-1.13` (or `typesafe/jev-latest`). Also a direct Python SDK (`typesafe-sdk`) and a JavaScript SDK.

### Documented weaknesses — TypeSafe publishes a "jaggedness" page, take it seriously
1. **Literal reading** — answers as written; poor with scoping words, negations, implied conditions.
2. **Math and numbers** — "Jev is not a calculator." Bad at counting, tallying, hex/RGB.
3. **Dates and time** — "reads dates as text, not as ordered quantities." Cannot order dates, compute durations, or test windows.
4. **Indirection** — multi-hop reasoning, properties-of-properties, double negatives degrade it.
5. **Large state with irrelevant detail** — distractors cause context rot.
6. **Adversarial content** — no default defence against injected instructions.
7. **Contradictory instructions vs criteria** — degrades badly.
8. **No structural invariants** — negations are not guaranteed to sum to one.
9. **No generation** — "Jev is not trained to generate text."
Also: **text only** (no images/audio/video yet), and English is substantially stronger than other languages.

## The mental-model question I actually want answered

The cheap framing is "fast classifier." I think that undersells it, and I want to know whether I'm right. The real shift may be that **a calibrated semantic judgement now costs about what an if-statement costs** — ~100ms, effectively free, schema-guaranteed, with an honest probability attached. Things that were impossible when judgement cost 3 seconds and a cent:
- semantic predicates inside a hot loop or a real-time tick
- a *dense field* of thousands of judgements over a corpus, continuously maintained
- speculative evaluation of branches you probably won't take
- a calibrated scalar (Score) used as a **continuous control signal** rather than a label
- confidence itself as the control flow — route, escalate, or halt on the probability

## What I want from you

**A. The mental model.** In your own framing, what IS this thing? Give me the sharpest analogy you can defend, and say explicitly what it is NOT. What is the class of problem that just became tractable? Where is my framing above wrong or lazy?

**B. The non-obvious capability.** What can you do with Choice/Score/Noul + free fan-out + 100ms + calibrated probabilities that is NOT "classify support tickets faster"? Push hard. I want the thing nobody has thought of yet because the model is four days old.

**C. Three hackathon ideas** that are only possible because of Jev — where an LLM-based version would be too slow, too expensive, or too unreliable to demo. For each: what it is, why Jev specifically unlocks it, and what the live demo looks like. Remember the constraints: built in ~8.5 hours by a team formed that morning, demoed live in 3 minutes on stage, judged by Google DeepMind, Conduct (enterprise AI operating systems), Modal (compute) and Pydantic (typed agents + Logfire).

**D. The trap.** What is the seductive-but-wrong way to use this? Where will people misuse it, and what does the jaggedness list tell you about which demos will embarrass someone on stage?

Be concrete and opinionated. No preamble.

YOUR LENS: **Systems engineer.** What does this change about how you ARCHITECT an agent? Today agents are slow serial LLM loops where every judgement is a costly round-trip, so we batch, cache and avoid asking. If judgement is 100ms and free, the architecture inverts: you can judge constantly, judge everything, judge speculatively. Sketch the agent architecture that becomes correct under these economics and explain what it replaces. Be concrete about where Jev sits next to an LLM in a hybrid system - which decisions go to which, and why.
warning: clamping SessionEnd hook timeout to 3s in /Users/mustafatokmak-st/.codex/plugins/cache/openai-codex/codex/1.0.6/hooks/hooks.json
2026-09-19T06:08:00.063166Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://mcp.context7.com/.well-known/oauth-protected-resource\"" })
warning: Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart
hook: SessionStart Completed
hook: SessionStart Completed
codex
## A. The mental model

Jev is a **probabilistic semantic branch unit**.

The closest systems analogy is a CPU branch predictor crossed with a typed sensor:

- A sensor converts messy physical reality into structured measurements.
- A branch predictor estimates which control path should execute.
- Jev converts messy textual state into a typed vector of semantic measurements and branch probabilities.

An LLM answers, “What should I say or do next?” Jev answers, in parallel:

- Which state are we probably in?
- Which transitions are currently enabled?
- How strongly does each condition hold?
- How confident should the runtime be?
- Is this uncertain enough to leave the fast path?

That makes it less like a small LLM and more like a **semantic coprocessor for control flow**.

A useful abstraction is:

```text
Jev: unstructured state → typed probability vector
```

The output is not an answer. It is a set of signals with which ordinary software can make an answer, select a policy, schedule work, or interrupt another model.

### What it is not

It is not:

- A deterministic predicate. A 0.97 Noul is not `true`.
- A planner, calculator, database, temporal engine, or theorem prover.
- A security boundary. Adversarial text can manipulate it.
- A replacement for an LLM when new language, explanations, plans, or code must be generated.
- A guarantee that several answers form a coherent worldview. Questions are evaluated independently; cross-question invariants do not arise automatically.
- A magic scalar oracle. A Score is interpolated ordinal judgement, not necessarily a linear physical quantity.

### What just became tractable

The new class of tractable problem is:

> High-frequency, reversible control over textual or semantic state, where each decision has a closed output space and occasional mistakes can be absorbed by thresholds, hysteresis, escalation, or rollback.

Previously, semantic judgement was something an agent reluctantly requested at major decision points. Now it can be part of every state transition.

That enables:

- Semantic guards inside event loops.
- Per-message and per-tool-call supervision.
- Continuously maintained semantic indexes.
- Probabilistic finite-state machines whose transition guards are learned predicates.
- Dense observability: hundreds of measurements attached to every agent event.
- Speculative branch evaluation before the branch is selected.
- Graceful autonomy: confidence determines how much authority an agent receives.

### Where the “if-statement” framing is too generous

“A semantic judgement costs what an if-statement costs” captures the architectural inversion, but not the operational semantics.

An `if` statement is exact, local, effectively instantaneous, deterministic, and composable. Jev is remote, approximately 100ms, stochastic, distribution-sensitive, and potentially inconsistent across questions.

A better formulation is:

> A semantic judgement has become cheap enough to use like telemetry.

Telemetry is sampled constantly, influences control systems, and can trigger actions—but engineers do not confuse it with ground truth.

Two other corrections:

1. **“Judge everything” does not mean “put everything into one enormous state.”** Jev’s documented context-rot weakness means the correct architecture is many small, purpose-built observations, not an omniscient context blob.
2. **Calibration is useful only under the distribution where it remains calibrated.** Confidence should be logged and tested against actual outcomes. A reported 0.9 is not automatically a production-grade 90% guarantee for your domain.

---

## B. The non-obvious capability

The important capability is not classification. It is the ability to build **probabilistic reactive programs over language**.

A conventional state machine has exact guards:

```python
if payment_received and inventory > 0:
    transition("FULFIL")
```

A Jev-backed state machine can have semantic guards:

```python
if safe_to_execute > 0.995 and
   request_is_unambiguous > 0.98 and
   action_is_reversible > 0.90:
    transition("EXECUTE")
elif clarification_would_help > 0.70:
    transition("ASK")
else:
    transition("HUMAN_REVIEW")
```

The novel part is that every possible guard can be evaluated before the runtime knows which branch it needs. The runtime receives a **branch-condition vector** in one pass.

That supports four architectural primitives.

### 1. Semantic interrupts

Jev can run alongside an agent and continuously test for conditions such as:

- The objective appears to have changed.
- New evidence contradicts the current plan.
- The agent is repeating itself.
- The proposed action exceeds the user’s apparent authority.
- Progress has stalled.
- A cheaper strategy is now viable.
- The current result is probably sufficient.

Crossing a threshold emits an interrupt: pause, re-plan, reduce authority, request clarification, or call the expensive model.

Today, agents usually discover these things when the next LLM call happens to notice them. A semantic interrupt fabric makes them runtime behavior.

This is supervision, not security: untrusted content must be separated or sanitized because Jev itself is not adversarially robust.

### 2. Confidence-shaped autonomy

Most agents use discrete permissions: autonomous or human-approved.

Jev enables a continuous autonomy budget:

```text
low confidence     → observe only
moderate confidence → draft
high confidence    → execute reversible action
very high confidence + policy checks → execute consequential action
```

This is more interesting than routing. The probability changes how much authority, compute, latency, or money the system allocates.

A Score can similarly control:

- Search breadth.
- Number of agents spawned.
- Verification depth.
- Tool timeout.
- Retry aggressiveness.
- Sampling frequency.
- Human-review priority.

The critical caveat is that Score levels should be treated as ordinal anchors. Do not assume the difference between 1.0 and 2.0 has the same meaning as 2.0 and 3.0 unless you validate that interpretation.

### 3. Semantic observability

Current traces tell you what an agent did. Jev can cheaply annotate every trace event with what the system appeared to be experiencing:

- ambiguity
- goal drift
- evidence sufficiency
- user frustration
- irreversibility
- policy tension
- novelty
- repetition
- likely completion
- need for escalation

That creates a dense semantic time series over an agent run.

You could ask questions that did not matter when the event occurred because their marginal latency is near zero. Weeks later, those stored signals let you explain failures, train routing policies, or discover recurring failure states without replaying every trace through an expensive LLM.

### 4. Probabilistic branch compilation

An agent workflow can declare all semantic guards for a state up front:

```python
questions = {
    "goal_changed": Noul(...),
    "has_enough_evidence": Noul(...),
    "action_reversible": Noul(...),
    "needs_clarification": Noul(...),
    "best_next_phase": Choice(...),
    "execution_risk": Score(...),
    "user_dissatisfaction": Score(...),
}
```

The application—not the model—then applies deterministic policy to the returned distribution.

This separates:

- Perception: Jev
- Policy and invariants: code
- Reasoning and generation: LLM
- Facts, numbers, dates, permissions: conventional systems

That separation is the architectural breakthrough.

---

## C. Three hackathon ideas

### 1. Semantic Flight Recorder: an agent runtime that knows when it is going wrong

#### What it is

A lightweight middleware layer around any tool-using agent. Every message, plan, tool proposal, tool result, and final response becomes an event.

For each event, Jev evaluates a fixed speculative panel:

- Has the user’s objective changed?
- Is the next action reversible?
- Does the action require confirmation?
- Is the agent stuck?
- Is it repeating a failed approach?
- Is evidence sufficient?
- Is the proposed answer premature?
- Would another tool call materially help?
- Is the observation relevant to the current objective?
- Which phase is the run in?
- How ambiguous is the current instruction?
- How likely is completion?

Code turns those answers into state transitions and interrupts.

#### Why Jev unlocks it

An LLM supervisor after every event would double or triple latency, accumulate meaningful cost, and itself produce untyped, variable explanations requiring parsing.

Jev can make supervision a permanent part of the event loop:

```text
event → Jev telemetry → policy → continue / pause / re-plan / escalate
```

Free fan-out matters because the runtime does not yet know which failure mode will matter. It asks all guards every time.

Pydantic defines the event and decision schemas. Logfire displays the probability traces. Modal can run many concurrent agent sessions or a replay benchmark. This naturally touches several judges’ domains without feeling bolted together.

#### Three-minute live demo

1. Start an agent on a simple multi-tool task.
2. Show a live panel with 15–30 semantic signals updating after each event.
3. Mid-run, add an ambiguous instruction that appears to change the objective.
4. The `goal_changed` and `needs_clarification` probabilities rise; the runtime pauses rather than continuing the old plan.
5. Clarify the objective. The signals fall, authority is restored, and the run continues.
6. Replay the same trace at high speed and show the semantic timeline locating the exact moment the run destabilized.

The punchline:

> We did not build another agent. We built the control system agents were missing.

This is the strongest of the three ideas.

---

### 2. Semantic Scheduler: a real-time operating system for a swarm of agents

#### What it is

A scheduler that receives a stream of tasks and continuously decides:

- Which worker is the best fit?
- Is the task sufficiently specified?
- Can it run concurrently?
- Does it conflict with another task?
- Is its latest result useful?
- Should it be retried, split, cancelled, escalated, or merged?
- How much compute and verification does it deserve?

Each task-worker pair gets typed semantic signals. Ordinary code combines them with exact measurements such as queue depth, cost, deadlines, permissions, and worker availability.

Jev supplies judgement; the scheduler supplies invariants.

#### Why Jev unlocks it

LLM-based orchestration is typically serialized:

```text
inspect task → choose agent → wait → inspect result → decide next step
```

That makes the orchestrator a latency bottleneck.

A Jev scheduler can evaluate every plausible decision at each tick, including speculative ones:

```text
task event
    ↓
all routing, sufficiency, conflict, retry and escalation predicates
    ↓
deterministic scheduling policy
```

The system can re-evaluate continuously when task descriptions or worker results change. The demo would be prohibitively sluggish if every scheduling tick required an LLM completion.

#### Three-minute live demo

1. Display five specialist workers and a queue of 20 incoming tasks.
2. Stream tasks into the system while the scheduler’s routing probabilities animate.
3. Introduce one vague task, one duplicate, and one result that superficially looks finished but lacks evidence.
4. Show the scheduler asking for clarification, merging the duplicate, and returning the weak result for verification.
5. Change the operating policy from “minimize latency” to “minimize risk.” The same semantic measurements now produce different deterministic scheduling decisions.
6. Compare against a serial LLM router that has processed only a few tasks while the Jev scheduler has continuously reconsidered the whole active queue.

Do not ask Jev to reason about exact deadlines, costs, or token totals. Those belong in code.

---

### 3. Living Semantic Index: a database whose rows continuously acquire judgement

#### What it is

Take a corpus—support conversations, agent traces, incident reports, sales notes, or GitHub issues—and attach a large vector of typed semantic properties to every item:

- likely customer impact
- novelty
- actionability
- evidence quality
- urgency
- similarity of underlying failure mode
- whether the workaround is acceptable
- whether engineering action is needed
- likely responsible area
- confidence that the report is complete

This is not embedding similarity. Each dimension is an explicit, inspectable question with a probability or Score.

As new events arrive, only affected records are re-evaluated. The result is a continuously updated semantic materialized view.

#### Why Jev unlocks it

With an LLM, teams choose a few labels, process the corpus offline, and avoid recomputation. Jev’s economics encourage the opposite:

- Ask dozens of questions per record.
- Include speculative dimensions that may become useful later.
- Refresh affected records continuously.
- Preserve uncertainty rather than collapsing every row to a hard label.

The unexpected capability is querying the corpus by combinations of semantic conditions:

```text
high impact
AND probably novel
AND weak evidence
AND likely reproducible
AND low confidence in ownership
```

That is closer to an OLAP cube over judgement than a classifier.

#### Three-minute live demo

1. Load a few hundred synthetic or public agent-run incidents.
2. Show the semantic field populating in seconds, with probabilities rather than hard tags.
3. Stream in a new incident.
4. Watch it move through views as evidence is appended.
5. Select “high impact, uncertain owner, likely duplicate.” The dashboard instantly exposes the ambiguous cluster.
6. Open one row and show that 40–100 questions were evaluated together, while the application used only six for the current view.

Keep every record’s state small and focused. Packing the whole corpus into one prompt would directly trigger the documented irrelevant-context weakness.

---

## The hybrid agent architecture

The correct architecture is no longer a single model inside a serial loop.

```text
                         ┌─────────────────────────┐
events ──→ state reducer │ compact typed state     │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │ Jev semantic control     │
                         │                          │
                         │ Choice: state / route    │
                         │ Score: intensity / risk  │
                         │ Noul: transition guards  │
                         └────────────┬────────────┘
                                      │ probability vector
                         ┌────────────▼────────────┐
                         │ deterministic policy     │
                         │                          │
                         │ thresholds               │
                         │ hysteresis               │
                         │ permissions              │
                         │ budgets                  │
                         │ invariants               │
                         └──────┬─────────┬─────────┘
                                │         │
                          fast path       slow path
                                │         │
                         tools / wait     LLM reasoning,
                         route / halt     planning, generation
                                │         │
                         └──────┴────┬────┘
                                     │
                                  new event
```

### Jev should decide

- Which known state best describes the observation.
- Whether a semantic condition appears to hold.
- How strongly an ordinal property is present.
- Whether confidence is too low for autonomous execution.
- Which predefined route, worker, workflow, or policy is most appropriate.
- Whether the slow path is probably necessary.
- Whether an agent’s state appears to have materially changed.

### The LLM should handle

- Producing new language, plans, code, explanations, or queries.
- Open-ended reasoning where possible answers cannot be enumerated.
- Synthesizing evidence across multiple steps.
- Recovering when no predefined state or route fits.
- Converting an ambiguous objective into candidate structured questions.
- Explaining consequential decisions to a person.

### Ordinary code should handle

- Arithmetic.
- Dates, time windows, ordering, and deadlines.
- Authentication and authorization.
- Exact policy rules and regulatory constraints.
- Database consistency.
- Rate limits and budgets.
- Cross-answer invariants.
- Thresholds, hysteresis, retries, and rollback.
- Sanitization and separation of untrusted content.

What this replaces is the monolithic ReAct-style loop in which one LLM simultaneously perceives state, interprets policy, selects a tool, generates arguments, judges the result, and decides whether it is finished.

The replacement is a **two-speed agent**:

- Jev is the always-on reflex and telemetry layer.
- Deterministic code is the skeleton.
- The LLM is the expensive deliberative cortex invoked when genuine reasoning or generation is required.

---

## D. The trap

The seductive mistake is to treat Jev as an extremely fast, extremely cheap general intelligence API.

That produces demos where Jev is asked to:

- Interpret a long policy handbook and determine compliance.
- Calculate financial risk from numbers.
- Reason about dates and deadlines.
- Follow chains of indirect facts.
- Detect prompt injection.
- Produce mutually consistent answers across dozens of questions.
- Read a massive context containing every fact “just in case.”
- Convert a Score directly into money, temperature, time, or another linear control value.
- Make irreversible decisions because its confidence is high.

Those demos will work on the rehearsed happy path and fail under the first adversarial audience example.

### Specific stage-demo failure modes

**Negation trap**

“Is there no reason not to reject this?” is exactly the kind of wording likely to produce embarrassment. Rewrite criteria as positive, literal conditions.

**Date trap**

A demo that asks whether a contract expired, whether an incident is within a seven-day window, or which event happened first is delegating deterministic work to the model’s documented weakness.

Parse dates in code, compute the result, and pass Jev a named boolean or duration category if semantic judgement is still needed.

**Counting trap**

“Escalate if three or more customers reported this” must be computed outside Jev. Pass `report_count: 4`; do not ask it to tally messages.

**Context-dump trap**

Feeding an entire Slack channel, policy library, and agent trace into one state will create a flashy but unstable demo. Use a state reducer that constructs a compact JSON observation for each decision family.

**Security trap**

A malicious document can contain text designed to influence the judgement. Jev’s confidence does not make it an injection detector or authorization layer. Untrusted text must never be allowed to redefine the questions, criteria, or policy.

**False-continuity trap**

A Score of `1.8` is not automatically “twice as risky” as `0.9`. It is an interpolation between described ordinal levels. Use bands and validate them empirically.

**Independent-answer trap**

These may all simultaneously receive high probabilities:

- “Execute automatically.”
- “Ask for clarification.”
- “Escalate to a human.”

That is not necessarily a schema error. The policy layer must resolve conflicts explicitly.

**Threshold-flapping trap**

If the system executes at `p > 0.8` and pauses below it, small changes around 0.8 can cause oscillation. Use hysteresis:

```text
enter autonomous mode above 0.90
remain autonomous until below 0.75
```

Also require repeated observations for consequential transitions.

The winning demo should therefore make Jev visibly good at what it is: **fast semantic sensing feeding typed, deterministic control**. The losing demo will ask it to impersonate an LLM, a calculator, or a policy engine.
hook: Stop
hook: Stop Completed
tokens used
18,566
## A. The mental model

Jev is a **probabilistic semantic branch unit**.

The closest systems analogy is a CPU branch predictor crossed with a typed sensor:

- A sensor converts messy physical reality into structured measurements.
- A branch predictor estimates which control path should execute.
- Jev converts messy textual state into a typed vector of semantic measurements and branch probabilities.

An LLM answers, “What should I say or do next?” Jev answers, in parallel:

- Which state are we probably in?
- Which transitions are currently enabled?
- How strongly does each condition hold?
- How confident should the runtime be?
- Is this uncertain enough to leave the fast path?

That makes it less like a small LLM and more like a **semantic coprocessor for control flow**.

A useful abstraction is:

```text
Jev: unstructured state → typed probability vector
```

The output is not an answer. It is a set of signals with which ordinary software can make an answer, select a policy, schedule work, or interrupt another model.

### What it is not

It is not:

- A deterministic predicate. A 0.97 Noul is not `true`.
- A planner, calculator, database, temporal engine, or theorem prover.
- A security boundary. Adversarial text can manipulate it.
- A replacement for an LLM when new language, explanations, plans, or code must be generated.
- A guarantee that several answers form a coherent worldview. Questions are evaluated independently; cross-question invariants do not arise automatically.
- A magic scalar oracle. A Score is interpolated ordinal judgement, not necessarily a linear physical quantity.

### What just became tractable

The new class of tractable problem is:

> High-frequency, reversible control over textual or semantic state, where each decision has a closed output space and occasional mistakes can be absorbed by thresholds, hysteresis, escalation, or rollback.

Previously, semantic judgement was something an agent reluctantly requested at major decision points. Now it can be part of every state transition.

That enables:

- Semantic guards inside event loops.
- Per-message and per-tool-call supervision.
- Continuously maintained semantic indexes.
- Probabilistic finite-state machines whose transition guards are learned predicates.
- Dense observability: hundreds of measurements attached to every agent event.
- Speculative branch evaluation before the branch is selected.
- Graceful autonomy: confidence determines how much authority an agent receives.

### Where the “if-statement” framing is too generous

“A semantic judgement costs what an if-statement costs” captures the architectural inversion, but not the operational semantics.

An `if` statement is exact, local, effectively instantaneous, deterministic, and composable. Jev is remote, approximately 100ms, stochastic, distribution-sensitive, and potentially inconsistent across questions.

A better formulation is:

> A semantic judgement has become cheap enough to use like telemetry.

Telemetry is sampled constantly, influences control systems, and can trigger actions—but engineers do not confuse it with ground truth.

Two other corrections:

1. **“Judge everything” does not mean “put everything into one enormous state.”** Jev’s documented context-rot weakness means the correct architecture is many small, purpose-built observations, not an omniscient context blob.
2. **Calibration is useful only under the distribution where it remains calibrated.** Confidence should be logged and tested against actual outcomes. A reported 0.9 is not automatically a production-grade 90% guarantee for your domain.

---

## B. The non-obvious capability

The important capability is not classification. It is the ability to build **probabilistic reactive programs over language**.

A conventional state machine has exact guards:

```python
if payment_received and inventory > 0:
    transition("FULFIL")
```

A Jev-backed state machine can have semantic guards:

```python
if safe_to_execute > 0.995 and
   request_is_unambiguous > 0.98 and
   action_is_reversible > 0.90:
    transition("EXECUTE")
elif clarification_would_help > 0.70:
    transition("ASK")
else:
    transition("HUMAN_REVIEW")
```

The novel part is that every possible guard can be evaluated before the runtime knows which branch it needs. The runtime receives a **branch-condition vector** in one pass.

That supports four architectural primitives.

### 1. Semantic interrupts

Jev can run alongside an agent and continuously test for conditions such as:

- The objective appears to have changed.
- New evidence contradicts the current plan.
- The agent is repeating itself.
- The proposed action exceeds the user’s apparent authority.
- Progress has stalled.
- A cheaper strategy is now viable.
- The current result is probably sufficient.

Crossing a threshold emits an interrupt: pause, re-plan, reduce authority, request clarification, or call the expensive model.

Today, agents usually discover these things when the next LLM call happens to notice them. A semantic interrupt fabric makes them runtime behavior.

This is supervision, not security: untrusted content must be separated or sanitized because Jev itself is not adversarially robust.

### 2. Confidence-shaped autonomy

Most agents use discrete permissions: autonomous or human-approved.

Jev enables a continuous autonomy budget:

```text
low confidence     → observe only
moderate confidence → draft
high confidence    → execute reversible action
very high confidence + policy checks → execute consequential action
```

This is more interesting than routing. The probability changes how much authority, compute, latency, or money the system allocates.

A Score can similarly control:

- Search breadth.
- Number of agents spawned.
- Verification depth.
- Tool timeout.
- Retry aggressiveness.
- Sampling frequency.
- Human-review priority.

The critical caveat is that Score levels should be treated as ordinal anchors. Do not assume the difference between 1.0 and 2.0 has the same meaning as 2.0 and 3.0 unless you validate that interpretation.

### 3. Semantic observability

Current traces tell you what an agent did. Jev can cheaply annotate every trace event with what the system appeared to be experiencing:

- ambiguity
- goal drift
- evidence sufficiency
- user frustration
- irreversibility
- policy tension
- novelty
- repetition
- likely completion
- need for escalation

That creates a dense semantic time series over an agent run.

You could ask questions that did not matter when the event occurred because their marginal latency is near zero. Weeks later, those stored signals let you explain failures, train routing policies, or discover recurring failure states without replaying every trace through an expensive LLM.

### 4. Probabilistic branch compilation

An agent workflow can declare all semantic guards for a state up front:

```python
questions = {
    "goal_changed": Noul(...),
    "has_enough_evidence": Noul(...),
    "action_reversible": Noul(...),
    "needs_clarification": Noul(...),
    "best_next_phase": Choice(...),
    "execution_risk": Score(...),
    "user_dissatisfaction": Score(...),
}
```

The application—not the model—then applies deterministic policy to the returned distribution.

This separates:

- Perception: Jev
- Policy and invariants: code
- Reasoning and generation: LLM
- Facts, numbers, dates, permissions: conventional systems

That separation is the architectural breakthrough.

---

## C. Three hackathon ideas

### 1. Semantic Flight Recorder: an agent runtime that knows when it is going wrong

#### What it is

A lightweight middleware layer around any tool-using agent. Every message, plan, tool proposal, tool result, and final response becomes an event.

For each event, Jev evaluates a fixed speculative panel:

- Has the user’s objective changed?
- Is the next action reversible?
- Does the action require confirmation?
- Is the agent stuck?
- Is it repeating a failed approach?
- Is evidence sufficient?
- Is the proposed answer premature?
- Would another tool call materially help?
- Is the observation relevant to the current objective?
- Which phase is the run in?
- How ambiguous is the current instruction?
- How likely is completion?

Code turns those answers into state transitions and interrupts.

#### Why Jev unlocks it

An LLM supervisor after every event would double or triple latency, accumulate meaningful cost, and itself produce untyped, variable explanations requiring parsing.

Jev can make supervision a permanent part of the event loop:

```text
event → Jev telemetry → policy → continue / pause / re-plan / escalate
```

Free fan-out matters because the runtime does not yet know which failure mode will matter. It asks all guards every time.

Pydantic defines the event and decision schemas. Logfire displays the probability traces. Modal can run many concurrent agent sessions or a replay benchmark. This naturally touches several judges’ domains without feeling bolted together.

#### Three-minute live demo

1. Start an agent on a simple multi-tool task.
2. Show a live panel with 15–30 semantic signals updating after each event.
3. Mid-run, add an ambiguous instruction that appears to change the objective.
4. The `goal_changed` and `needs_clarification` probabilities rise; the runtime pauses rather than continuing the old plan.
5. Clarify the objective. The signals fall, authority is restored, and the run continues.
6. Replay the same trace at high speed and show the semantic timeline locating the exact moment the run destabilized.

The punchline:

> We did not build another agent. We built the control system agents were missing.

This is the strongest of the three ideas.

---

### 2. Semantic Scheduler: a real-time operating system for a swarm of agents

#### What it is

A scheduler that receives a stream of tasks and continuously decides:

- Which worker is the best fit?
- Is the task sufficiently specified?
- Can it run concurrently?
- Does it conflict with another task?
- Is its latest result useful?
- Should it be retried, split, cancelled, escalated, or merged?
- How much compute and verification does it deserve?

Each task-worker pair gets typed semantic signals. Ordinary code combines them with exact measurements such as queue depth, cost, deadlines, permissions, and worker availability.

Jev supplies judgement; the scheduler supplies invariants.

#### Why Jev unlocks it

LLM-based orchestration is typically serialized:

```text
inspect task → choose agent → wait → inspect result → decide next step
```

That makes the orchestrator a latency bottleneck.

A Jev scheduler can evaluate every plausible decision at each tick, including speculative ones:

```text
task event
    ↓
all routing, sufficiency, conflict, retry and escalation predicates
    ↓
deterministic scheduling policy
```

The system can re-evaluate continuously when task descriptions or worker results change. The demo would be prohibitively sluggish if every scheduling tick required an LLM completion.

#### Three-minute live demo

1. Display five specialist workers and a queue of 20 incoming tasks.
2. Stream tasks into the system while the scheduler’s routing probabilities animate.
3. Introduce one vague task, one duplicate, and one result that superficially looks finished but lacks evidence.
4. Show the scheduler asking for clarification, merging the duplicate, and returning the weak result for verification.
5. Change the operating policy from “minimize latency” to “minimize risk.” The same semantic measurements now produce different deterministic scheduling decisions.
6. Compare against a serial LLM router that has processed only a few tasks while the Jev scheduler has continuously reconsidered the whole active queue.

Do not ask Jev to reason about exact deadlines, costs, or token totals. Those belong in code.

---

### 3. Living Semantic Index: a database whose rows continuously acquire judgement

#### What it is

Take a corpus—support conversations, agent traces, incident reports, sales notes, or GitHub issues—and attach a large vector of typed semantic properties to every item:

- likely customer impact
- novelty
- actionability
- evidence quality
- urgency
- similarity of underlying failure mode
- whether the workaround is acceptable
- whether engineering action is needed
- likely responsible area
- confidence that the report is complete

This is not embedding similarity. Each dimension is an explicit, inspectable question with a probability or Score.

As new events arrive, only affected records are re-evaluated. The result is a continuously updated semantic materialized view.

#### Why Jev unlocks it

With an LLM, teams choose a few labels, process the corpus offline, and avoid recomputation. Jev’s economics encourage the opposite:

- Ask dozens of questions per record.
- Include speculative dimensions that may become useful later.
- Refresh affected records continuously.
- Preserve uncertainty rather than collapsing every row to a hard label.

The unexpected capability is querying the corpus by combinations of semantic conditions:

```text
high impact
AND probably novel
AND weak evidence
AND likely reproducible
AND low confidence in ownership
```

That is closer to an OLAP cube over judgement than a classifier.

#### Three-minute live demo

1. Load a few hundred synthetic or public agent-run incidents.
2. Show the semantic field populating in seconds, with probabilities rather than hard tags.
3. Stream in a new incident.
4. Watch it move through views as evidence is appended.
5. Select “high impact, uncertain owner, likely duplicate.” The dashboard instantly exposes the ambiguous cluster.
6. Open one row and show that 40–100 questions were evaluated together, while the application used only six for the current view.

Keep every record’s state small and focused. Packing the whole corpus into one prompt would directly trigger the documented irrelevant-context weakness.

---

## The hybrid agent architecture

The correct architecture is no longer a single model inside a serial loop.

```text
                         ┌─────────────────────────┐
events ──→ state reducer │ compact typed state     │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │ Jev semantic control     │
                         │                          │
                         │ Choice: state / route    │
                         │ Score: intensity / risk  │
                         │ Noul: transition guards  │
                         └────────────┬────────────┘
                                      │ probability vector
                         ┌────────────▼────────────┐
                         │ deterministic policy     │
                         │                          │
                         │ thresholds               │
                         │ hysteresis               │
                         │ permissions              │
                         │ budgets                  │
                         │ invariants               │
                         └──────┬─────────┬─────────┘
                                │         │
                          fast path       slow path
                                │         │
                         tools / wait     LLM reasoning,
                         route / halt     planning, generation
                                │         │
                         └──────┴────┬────┘
                                     │
                                  new event
```

### Jev should decide

- Which known state best describes the observation.
- Whether a semantic condition appears to hold.
- How strongly an ordinal property is present.
- Whether confidence is too low for autonomous execution.
- Which predefined route, worker, workflow, or policy is most appropriate.
- Whether the slow path is probably necessary.
- Whether an agent’s state appears to have materially changed.

### The LLM should handle

- Producing new language, plans, code, explanations, or queries.
- Open-ended reasoning where possible answers cannot be enumerated.
- Synthesizing evidence across multiple steps.
- Recovering when no predefined state or route fits.
- Converting an ambiguous objective into candidate structured questions.
- Explaining consequential decisions to a person.

### Ordinary code should handle

- Arithmetic.
- Dates, time windows, ordering, and deadlines.
- Authentication and authorization.
- Exact policy rules and regulatory constraints.
- Database consistency.
- Rate limits and budgets.
- Cross-answer invariants.
- Thresholds, hysteresis, retries, and rollback.
- Sanitization and separation of untrusted content.

What this replaces is the monolithic ReAct-style loop in which one LLM simultaneously perceives state, interprets policy, selects a tool, generates arguments, judges the result, and decides whether it is finished.

The replacement is a **two-speed agent**:

- Jev is the always-on reflex and telemetry layer.
- Deterministic code is the skeleton.
- The LLM is the expensive deliberative cortex invoked when genuine reasoning or generation is required.

---

## D. The trap

The seductive mistake is to treat Jev as an extremely fast, extremely cheap general intelligence API.

That produces demos where Jev is asked to:

- Interpret a long policy handbook and determine compliance.
- Calculate financial risk from numbers.
- Reason about dates and deadlines.
- Follow chains of indirect facts.
- Detect prompt injection.
- Produce mutually consistent answers across dozens of questions.
- Read a massive context containing every fact “just in case.”
- Convert a Score directly into money, temperature, time, or another linear control value.
- Make irreversible decisions because its confidence is high.

Those demos will work on the rehearsed happy path and fail under the first adversarial audience example.

### Specific stage-demo failure modes

**Negation trap**

“Is there no reason not to reject this?” is exactly the kind of wording likely to produce embarrassment. Rewrite criteria as positive, literal conditions.

**Date trap**

A demo that asks whether a contract expired, whether an incident is within a seven-day window, or which event happened first is delegating deterministic work to the model’s documented weakness.

Parse dates in code, compute the result, and pass Jev a named boolean or duration category if semantic judgement is still needed.

**Counting trap**

“Escalate if three or more customers reported this” must be computed outside Jev. Pass `report_count: 4`; do not ask it to tally messages.

**Context-dump trap**

Feeding an entire Slack channel, policy library, and agent trace into one state will create a flashy but unstable demo. Use a state reducer that constructs a compact JSON observation for each decision family.

**Security trap**

A malicious document can contain text designed to influence the judgement. Jev’s confidence does not make it an injection detector or authorization layer. Untrusted text must never be allowed to redefine the questions, criteria, or policy.

**False-continuity trap**

A Score of `1.8` is not automatically “twice as risky” as `0.9`. It is an interpolation between described ordinal levels. Use bands and validate them empirically.

**Independent-answer trap**

These may all simultaneously receive high probabilities:

- “Execute automatically.”
- “Ask for clarification.”
- “Escalate to a human.”

That is not necessarily a schema error. The policy layer must resolve conflicts explicitly.

**Threshold-flapping trap**

If the system executes at `p > 0.8` and pauses below it, small changes around 0.8 can cause oscillation. Use hysteresis:

```text
enter autonomous mode above 0.90
remain autonomous until below 0.75
```

Also require repeated observations for consequential transitions.

The winning demo should therefore make Jev visibly good at what it is: **fast semantic sensing feeding typed, deterministic control**. The losing demo will ask it to impersonate an LLM, a calculator, or a policy engine.
