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
