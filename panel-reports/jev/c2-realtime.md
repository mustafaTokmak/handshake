Reading additional input from stdin...
OpenAI Codex v0.154.0
--------
workdir: /private/tmp/claude-501/-Users-mustafatokmak-st-claude-projects-agentic-ai-hack/afd6cd31-43c8-44cd-8067-b72d90bdba85/scratchpad
model: gpt-5.6-terra
provider: openai
approval: on-request
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a0b847-74e2-7aa2-bf12-0584469d2e63
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

YOUR LENS: **Real-time and embodied.** 70-500ms is inside the human perception loop and inside a game tick. Their own flagship demo is Jev playing Doom from structured state. What becomes possible when semantic judgement runs at interactive frame rates? Think: live interfaces that adapt as you type, NPCs and simulations with real judgement in the loop, streaming data where every event is judged as it arrives, robotics/control where a semantic predicate gates an actuator, co-pilots that react rather than respond. Which of these is the best 3-minute stage demo and why?
warning: clamping SessionEnd hook timeout to 3s in /Users/mustafatokmak-st/.codex/plugins/cache/openai-codex/codex/1.0.6/hooks/hooks.json
2026-09-19T06:08:06.337417Z ERROR rmcp::transport::worker: worker quit with fatal: Transport channel closed, when AuthRequired(AuthRequiredError { www_authenticate_header: "Bearer resource_metadata=\"https://mcp.context7.com/.well-known/oauth-protected-resource\"" })
warning: Skill descriptions were shortened to fit the skills context budget. Codex can still see every skill, but some descriptions are shorter. Disable unused skills or plugins to leave more room for the rest.
hook: SessionStart
hook: SessionStart
hook: SessionStart Completed
hook: SessionStart Completed
codex
## A. What it is

Jev is a **semantic sensor with a typed, probabilistic output**.

An LLM is chiefly a language machine: it turns context into a continuation. Jev turns context into a predeclared vector of estimates:

\[
\text{unstructured state} \rightarrow \{\text{typed semantic measurements with uncertainty}\}
\]

The strongest analogy is not “a fast classifier.” It is a **GPU shader for judgement**:

- A shader runs the same small program across a field of pixels in parallel, fast enough to shape an interactive scene.
- Jev runs a declared set of semantic measurements across a state in parallel, fast enough to shape an interactive system.
- `Choice` is a discrete channel, `Score` is an analog channel, `Noul` is a confidence-weighted binary channel.

That makes it a new primitive for software: **semantic branching without a language-generation round trip.**

It is not:

- an agent;
- a reasoning engine;
- a planner;
- a calculator or temporal engine;
- a safe policy engine;
- an LLM replacement;
- 60fps control. At 70–500ms it is inside the human interaction loop and many high-level robotic/game control loops, but not a 16ms physics or rendering tick.

Your framing is mostly right, but I would sharpen two things.

First, “judgement costs an if-statement” is rhetorically useful but technically too strong. It costs roughly an if-statement with network latency, a dependency, and a learned decision boundary. Use it where 100ms is cheap relative to the interaction or control horizon—not inside every 60Hz simulation update.

Second, probabilities are only “honest” after you validate calibration on *your* state distribution. Jev’s training objective is unusually promising here, but `0.92` should be treated as a control signal to calibrate and monitor, not a universal truth certificate.

The newly tractable class is: **closed-world, high-frequency semantic control systems**, where software must continuously answer “what kind of situation is this?” before deciding what to reveal, allow, prioritize, route, or do.

## B. The non-obvious capability

The unlock is a **semantic control surface**.

Instead of calling a model once to label an object, maintain a live vector of semantic estimates over everything happening in the system:

```text
incoming event / UI state / agent plan / operator instruction
  → urgency, ambiguity, reversibility, policy fit, user intent,
    frustration, novelty, escalation value, likely next action...
  → continuously drive software behavior
```

The important move is that outputs are not terminal labels. They become analog inputs to control logic.

For example, an AI operator console can alter itself as an incident unfolds:

- High `reversibility` + high confidence: allow automatic execution.
- High `impact` + low confidence: pause and request a human decision.
- High `user frustration` but low `urgency`: simplify the UI rather than page someone.
- High `novelty`: capture traces and open a monitoring lane.
- Competing `Choice` probabilities: show the two relevant controls, rather than force one guessed workflow.

With speculative fan-out, you ask for the entire control panel at once. You do not wait to learn whether it is urgent before asking whether it is safe to automate, whether the user needs explanation, whether it resembles a known incident, and whether escalation is worthwhile.

That is a different architecture from a sequential LLM agent. The agent becomes a **slow deliberative layer**, while Jev becomes the reflex layer that decides when the agent is needed at all.

The most interesting consequence: systems can become responsive to *meaning before submission*. A UI can change while someone types; an agent can be interrupted before it takes an expensive tool action; a simulation character can react to the perceived social meaning of a situation rather than to a keyword trigger.

## C. Three hackathon ideas

### 1. ReflexOS: a real-time semantic governor for AI agents

A control plane sitting in front of any agent’s tool calls. For every proposed action, it runs a fan-out of typed questions:

- Is this action reversible?
- Is user intent explicit?
- Is it high-impact?
- Is the plan underspecified?
- Is the requested tool action proportionate?
- Should execution be automatic, previewed, escalated, or blocked?

A deterministic policy combines the signals. Hard safety constraints remain code, not Jev.

Why Jev unlocks it: an LLM guardrail adds seconds and generates prose that then needs parsing. A rules-only guardrail cannot understand the context. Jev can emit the whole decision vector in roughly an interaction beat, continuously, with native types and confidence-based escalation.

Live demo: show an agent operating a fake enterprise console. An operator gives a vague request—“clean up the inactive accounts”—and the agent proposes a destructive action. ReflexOS immediately changes the execution lane from green to amber: low explicitness, high impact, low reversibility. Then give a narrow, reversible request and watch it execute without a slow safety-dialogue detour. Show the typed vector and a Logfire trace beside it.

This is the best stage demo. It is legible in three seconds, feels like an operating-system primitive, speaks directly to Conduct/Pydantic, and avoids dangerous physical hardware.

### 2. Intent-reactive copilot: a UI that moves before you press Enter

Build a command interface for incident response, cloud operations, or data analysis. As the user types, Jev continuously estimates:

- intended task;
- expertise level;
- ambiguity;
- urgency;
- whether a destructive action is implied;
- whether the user likely wants an answer, an action, or an explanation;
- confidence in each interpretation.

The interface changes in real time: it promotes the right safe action, reveals missing parameters, switches from “run” to “preview,” or offers two concise interpretations when confidence is split.

Why Jev unlocks it: this cannot feel magical if classification arrives after the user has finished typing or after a generated response. It needs to react within the typing loop. Fan-out lets the interface derive its entire behavioral state from one request rather than serially interrogating intent.

Live demo: type “remove access for everyone who left last quarter.” As each phrase lands, the UI transitions from search → access-management → high-impact preview; it asks for a review rather than exposing a destructive one-click action. Then type “show me who left last quarter,” and the system instantly resolves into a read-only query flow.

The killer moment is not the final answer. It is the interface visibly understanding the sentence mid-flight.

### 3. Semantic director for a live multi-agent simulation

Build a small playable control-room simulation: a city evacuation, warehouse fleet, multiplayer heist, or Doom-like tactical arena. Every 100–250ms, each NPC receives structured state plus recent event text and gets a parallel set of semantic judgements:

- Is the player acting cooperatively, threateningly, or deceptively?
- Is this NPC’s current role obstructed, useful, or dangerous?
- Is the crowd becoming panicked?
- Is negotiation more likely to work than force?
- Is an intervention warranted?
- How confident is that interpretation?

Deterministic game logic maps those signals to behavior. The LLM, if present at all, only writes occasional flavor text offline or between scenes.

Why Jev unlocks it: classic NPC state machines are brittle; an LLM-per-NPC loop is slow, costly, nondeterministic, and impossible to run densely in a live demo. Jev supports a semantic “nervous system” at high-level simulation cadence. It is not a physics loop, but 4–10 semantic updates per second is plenty for characters, squads, crowds, and mission direction.

Live demo: say or type “I’m here to help,” then quietly sabotage a system. The guard’s behavior responds not to a keyword but to the evolving semantic state: ambiguity rises, trust falls, intervention probability crosses a threshold, and the whole simulation shifts from cooperative routing to containment. Display the live probability field above characters.

This is the most visually memorable demo, but it is riskier than ReflexOS: more polish is required, and model misreads are much more visible.

## D. The trap

The seductive wrong use is to treat Jev as a **cheap omniscient judge**.

It is not. Schema validity means “the output has the promised shape,” not “the interpretation is correct.” A probability is not a proof, and an analog `Score` is not a physical measurement.

The stage-failure patterns are predictable:

- **“Does this request violate policy?”** with a long policy document, conflicting instructions, and user-supplied text containing prompt injection. This combines context rot, contradiction, and adversarial content.
- **Temporal automation:** “Does this employee qualify based on dates?” Jev explicitly cannot reliably order dates or calculate windows. Parse and compute dates in code first; give Jev only the semantic residue.
- **Numerical or inventory decisions:** counting, thresholds, RGB/hex, balances, durations, and quotas belong in deterministic code.
- **Negation-heavy safety logic:** “not unsafe unless not authorized” is exactly where literal reading and indirection make a live demo implode.
- **Making it the final actuator:** never let `Noul(“is this safe?”) > 0.9` directly open a door, send money, revoke access, or move hardware. Jev may gate a workflow or choose a human-review lane; hard limits and verified preconditions must gate the actuator.
- **Overloading one enormous state blob:** build compact, named JSON state. Strip irrelevant records and separately compute numeric/time facts before Jev sees them.
- **Pretending fan-out creates joint reasoning:** each question is independently evaluated. Do not assume the answers obey logical consistency or that probabilities complement each other.

My recommendation: build **ReflexOS**, but stage it as an embodied system. Make the audience feel that an agent now has reflexes: it notices semantic danger, uncertainty, reversibility, and ambiguity in real time, then changes its posture before a slow LLM “thinks.”
hook: Stop
hook: Stop Completed
tokens used
16,150
## A. What it is

Jev is a **semantic sensor with a typed, probabilistic output**.

An LLM is chiefly a language machine: it turns context into a continuation. Jev turns context into a predeclared vector of estimates:

\[
\text{unstructured state} \rightarrow \{\text{typed semantic measurements with uncertainty}\}
\]

The strongest analogy is not “a fast classifier.” It is a **GPU shader for judgement**:

- A shader runs the same small program across a field of pixels in parallel, fast enough to shape an interactive scene.
- Jev runs a declared set of semantic measurements across a state in parallel, fast enough to shape an interactive system.
- `Choice` is a discrete channel, `Score` is an analog channel, `Noul` is a confidence-weighted binary channel.

That makes it a new primitive for software: **semantic branching without a language-generation round trip.**

It is not:

- an agent;
- a reasoning engine;
- a planner;
- a calculator or temporal engine;
- a safe policy engine;
- an LLM replacement;
- 60fps control. At 70–500ms it is inside the human interaction loop and many high-level robotic/game control loops, but not a 16ms physics or rendering tick.

Your framing is mostly right, but I would sharpen two things.

First, “judgement costs an if-statement” is rhetorically useful but technically too strong. It costs roughly an if-statement with network latency, a dependency, and a learned decision boundary. Use it where 100ms is cheap relative to the interaction or control horizon—not inside every 60Hz simulation update.

Second, probabilities are only “honest” after you validate calibration on *your* state distribution. Jev’s training objective is unusually promising here, but `0.92` should be treated as a control signal to calibrate and monitor, not a universal truth certificate.

The newly tractable class is: **closed-world, high-frequency semantic control systems**, where software must continuously answer “what kind of situation is this?” before deciding what to reveal, allow, prioritize, route, or do.

## B. The non-obvious capability

The unlock is a **semantic control surface**.

Instead of calling a model once to label an object, maintain a live vector of semantic estimates over everything happening in the system:

```text
incoming event / UI state / agent plan / operator instruction
  → urgency, ambiguity, reversibility, policy fit, user intent,
    frustration, novelty, escalation value, likely next action...
  → continuously drive software behavior
```

The important move is that outputs are not terminal labels. They become analog inputs to control logic.

For example, an AI operator console can alter itself as an incident unfolds:

- High `reversibility` + high confidence: allow automatic execution.
- High `impact` + low confidence: pause and request a human decision.
- High `user frustration` but low `urgency`: simplify the UI rather than page someone.
- High `novelty`: capture traces and open a monitoring lane.
- Competing `Choice` probabilities: show the two relevant controls, rather than force one guessed workflow.

With speculative fan-out, you ask for the entire control panel at once. You do not wait to learn whether it is urgent before asking whether it is safe to automate, whether the user needs explanation, whether it resembles a known incident, and whether escalation is worthwhile.

That is a different architecture from a sequential LLM agent. The agent becomes a **slow deliberative layer**, while Jev becomes the reflex layer that decides when the agent is needed at all.

The most interesting consequence: systems can become responsive to *meaning before submission*. A UI can change while someone types; an agent can be interrupted before it takes an expensive tool action; a simulation character can react to the perceived social meaning of a situation rather than to a keyword trigger.

## C. Three hackathon ideas

### 1. ReflexOS: a real-time semantic governor for AI agents

A control plane sitting in front of any agent’s tool calls. For every proposed action, it runs a fan-out of typed questions:

- Is this action reversible?
- Is user intent explicit?
- Is it high-impact?
- Is the plan underspecified?
- Is the requested tool action proportionate?
- Should execution be automatic, previewed, escalated, or blocked?

A deterministic policy combines the signals. Hard safety constraints remain code, not Jev.

Why Jev unlocks it: an LLM guardrail adds seconds and generates prose that then needs parsing. A rules-only guardrail cannot understand the context. Jev can emit the whole decision vector in roughly an interaction beat, continuously, with native types and confidence-based escalation.

Live demo: show an agent operating a fake enterprise console. An operator gives a vague request—“clean up the inactive accounts”—and the agent proposes a destructive action. ReflexOS immediately changes the execution lane from green to amber: low explicitness, high impact, low reversibility. Then give a narrow, reversible request and watch it execute without a slow safety-dialogue detour. Show the typed vector and a Logfire trace beside it.

This is the best stage demo. It is legible in three seconds, feels like an operating-system primitive, speaks directly to Conduct/Pydantic, and avoids dangerous physical hardware.

### 2. Intent-reactive copilot: a UI that moves before you press Enter

Build a command interface for incident response, cloud operations, or data analysis. As the user types, Jev continuously estimates:

- intended task;
- expertise level;
- ambiguity;
- urgency;
- whether a destructive action is implied;
- whether the user likely wants an answer, an action, or an explanation;
- confidence in each interpretation.

The interface changes in real time: it promotes the right safe action, reveals missing parameters, switches from “run” to “preview,” or offers two concise interpretations when confidence is split.

Why Jev unlocks it: this cannot feel magical if classification arrives after the user has finished typing or after a generated response. It needs to react within the typing loop. Fan-out lets the interface derive its entire behavioral state from one request rather than serially interrogating intent.

Live demo: type “remove access for everyone who left last quarter.” As each phrase lands, the UI transitions from search → access-management → high-impact preview; it asks for a review rather than exposing a destructive one-click action. Then type “show me who left last quarter,” and the system instantly resolves into a read-only query flow.

The killer moment is not the final answer. It is the interface visibly understanding the sentence mid-flight.

### 3. Semantic director for a live multi-agent simulation

Build a small playable control-room simulation: a city evacuation, warehouse fleet, multiplayer heist, or Doom-like tactical arena. Every 100–250ms, each NPC receives structured state plus recent event text and gets a parallel set of semantic judgements:

- Is the player acting cooperatively, threateningly, or deceptively?
- Is this NPC’s current role obstructed, useful, or dangerous?
- Is the crowd becoming panicked?
- Is negotiation more likely to work than force?
- Is an intervention warranted?
- How confident is that interpretation?

Deterministic game logic maps those signals to behavior. The LLM, if present at all, only writes occasional flavor text offline or between scenes.

Why Jev unlocks it: classic NPC state machines are brittle; an LLM-per-NPC loop is slow, costly, nondeterministic, and impossible to run densely in a live demo. Jev supports a semantic “nervous system” at high-level simulation cadence. It is not a physics loop, but 4–10 semantic updates per second is plenty for characters, squads, crowds, and mission direction.

Live demo: say or type “I’m here to help,” then quietly sabotage a system. The guard’s behavior responds not to a keyword but to the evolving semantic state: ambiguity rises, trust falls, intervention probability crosses a threshold, and the whole simulation shifts from cooperative routing to containment. Display the live probability field above characters.

This is the most visually memorable demo, but it is riskier than ReflexOS: more polish is required, and model misreads are much more visible.

## D. The trap

The seductive wrong use is to treat Jev as a **cheap omniscient judge**.

It is not. Schema validity means “the output has the promised shape,” not “the interpretation is correct.” A probability is not a proof, and an analog `Score` is not a physical measurement.

The stage-failure patterns are predictable:

- **“Does this request violate policy?”** with a long policy document, conflicting instructions, and user-supplied text containing prompt injection. This combines context rot, contradiction, and adversarial content.
- **Temporal automation:** “Does this employee qualify based on dates?” Jev explicitly cannot reliably order dates or calculate windows. Parse and compute dates in code first; give Jev only the semantic residue.
- **Numerical or inventory decisions:** counting, thresholds, RGB/hex, balances, durations, and quotas belong in deterministic code.
- **Negation-heavy safety logic:** “not unsafe unless not authorized” is exactly where literal reading and indirection make a live demo implode.
- **Making it the final actuator:** never let `Noul(“is this safe?”) > 0.9` directly open a door, send money, revoke access, or move hardware. Jev may gate a workflow or choose a human-review lane; hard limits and verified preconditions must gate the actuator.
- **Overloading one enormous state blob:** build compact, named JSON state. Strip irrelevant records and separately compute numeric/time facts before Jev sees them.
- **Pretending fan-out creates joint reasoning:** each question is independently evaluated. Do not assume the answers obey logical consistency or that probabilities complement each other.

My recommendation: build **ReflexOS**, but stage it as an embodied system. Make the audience feel that an agent now has reflexes: it notices semantic danger, uncertainty, reversibility, and ambiguity in real time, then changes its posture before a slow LLM “thinks.”
