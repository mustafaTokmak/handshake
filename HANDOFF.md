# HANDOFF — {Tech: Europe} Agentic AI Hack (London)

Written 2026-09-19. Continues in a fresh session.

## What this session did

Ran three multi-model panels to pick a project for the hackathon, then red-teamed the result, then re-evaluated everything against a new model class (TypeSafe's Jev) that launched 2026-09-15.

**29 agent runs total** across Claude (Opus/Sonnet), Codex (sol/terra), Grok 4.6 (×7), Kimi K3, DeepSeek v4.1, Muse, GLM, Gemini Flash.

## The event

"{Tech: Europe} Agentic AI Hack", London, one Saturday. Co-hosts **Google DeepMind** + **Conduct** (AI operating systems for enterprise software). Tech partners **Modal** + **Pydantic** (Pydantic AI / Logfire). Free credits from all partners. 70 participants, first-come.

Schedule: 09:30 doors · 10:00 opening + **matchmaking** (teams form on the day) · 12:30 lunch · **19:00 competition opt-in deadline** · 20:00 live demos · 20:45 awards.

=> ~8.5h build (10:30–19:00), team possibly of strangers, venue wifi, ~3 min live demo in front of the sponsors. **Exact calendar date was never confirmed** — the Luma page only said "Saturday". Worth pinning down.

## Documents produced (read in this order)

| File | What it is |
|---|---|
| `JEV-MENTAL-MODEL.md` | **Most recent and most important.** What Jev is, corrected mechanics, and why it changes the plan |
| `FINAL-BUILD-SPEC.md` | Red-teamed Unwind spec — hour-by-hour, demo script, failure modes |
| `IDEA-PANEL-VERDICT.md` | Round 1. Panel table + **cliché list** (still valuable: what 10+ other teams will build) |
| `panel-reports/` | All 30 raw agent reports + the three briefs. Preserved from the session scratchpad |

## Where the decision actually stands

**Round 1** → picked **Unwind** (an undo button for AI agents: ops agent wrecks a fake company overnight, Unwind classifies each effect reversible/compensable/irreversible, flags where a human has since edited the record, reverses what it safely can).

**Round 2 red team** (8 agents, voted 4 Unwind / 3 "intervene before the write" / 1 SIEGE) broke four things:
- The "inverse synthesiser" collapses to `restore(before)` — a lookup table with an LLM narrating it
- "Residual delta 0 of 12" is a **logic bomb** (you can't preserve a human edit *and* fail to unsend an email *and* report zero)
- Budget off by 40–100% (36–56 person-hours needed vs ~25–30 available)
- Cut order was backwards (GitHub revert is the only surface touching reality; it was first to cut)

Three agents wanted to intervene **before** the write (PRECHECK/Airlock/SHADOW). The judge simulation killed that: it files instantly into `terraform plan`/confirm-dialog, and *"if a human stamps every write, you have deleted the agent"* — approval-queue fatigue is what Conduct's customers already switched off.

**Jev round** resolved that deadlock. A **calibrated** gate doesn't queue everything — it acts autonomously when confident and halts only on the genuinely uncertain call. That was unbuildable before (an LLM gate on 14 serial tool calls = 20–40s of dead air).

**Current leading idea: "Breaker"** — a circuit breaker on the tool path. Same overnight wreck, but nothing commits. Each proposed write hits one Jev fan-out bundle (~150ms). Bars flash 0.97, 0.94, then **0.54 same-customer → HALT**; the termination email never leaves. Split screen: Gemini Flash returns `is_same_customer: true` in 3.1s on the same state. Python owns money/dates/IDs/commits; Gemini only plans and rewrites on halt.

**But see the open problem below — this needs one more decision before it's final.**

## The unresolved problem (start here)

`madewithjev.com` lists **180+ projects built in 4 days**. Three of them are already Breaker:
- **`pi-heed`** (@BowenXu) — "tool call verification against user intent" — this *is* Breaker's core
- **Jev as agent safety monitor** (@isNickMa) — "detects attacks more accurately than Gemini"
- **DiffJury** (@raihankhan_rk) — merge-safety assessment

The confidence-cascade architecture is also taken (@nutlope's fraud detection, cascading uncertain cases to a bigger model).

**What is still unclaimed**, from the same survey:
1. **Money arithmetic** — not one project multiplies a calibrated probability by a currency amount. `expected_loss = P(wrong_entity) × £4,200` is open, and it's what an enterprise buyer cares about.
2. **Robotics/devices** — 1 project total (`jev-drone`, 2.5Hz) vs 42 browser and 61 tools projects.
3. **Modal** — Cloudflare and Vercel shipped native Jev integrations; **Modal has none**. Modal is a judge. "Jev fan-out mapped across a Modal fleet" is an unoccupied intersection that also flatters a sponsor.

**Decision needed:** keep Breaker but re-pitch around expected-loss + Modal fleet (three unclaimed things stacked, same build), or pivot. Last user instruction was leaning toward reusing existing open-source repos as scaffolding — see "open questions".

## Jev — the facts that matter (full detail in `JEV-MENTAL-MODEL.md`)

```
PROBE : State × (Name ⇀ FiniteType) → ∏ᵢ Δ(τᵢ)
```
Declare types first; one parallel forward pass inhabits all of them; **extra questions are free**; you get back **a product of marginals, not a joint**. That last clause explains nearly the whole documented weakness list.

Three primitives: `Choice` (categorical + confidence), `Score` (float + per-level probs + confidence), `Noul` (**bare probability — no confidence field**).

**Corrections that were hard-won — do not re-derive:**
- `Noul` has **no** confidence field. Gate on `Choice`/`Score`.
- The `Score` float is a probability-weighted mean of **level numbers** — `1.035` = 96.5% level 1 / 3.5% level 2. It moves with *uncertainty*, not intensity. Monotone uses (rank, threshold, direction) sound; metric uses (differences, averages, PID) unsound.
- **Adjacency test:** mass on two *adjacent* levels totalling ≥0.90 = genuine interpolation. Wider = ignorance. Better than gating on `confidence`.
- More levels buy linearity/anchoring, **not resolution**. For clean magnitude use a **ladder of monotone threshold Nouls** (free under fan-out, gives the whole CDF, non-monotonicity = free rubric-validity check).
- Stability ("similar answers for similar inputs") holds over **state** variation with **criteria fixed**. Editing criteria *redefines the instrument* — invalidates thresholds and any time series across the edit. Hash `criteria + model version` as scale identity. **Never animate a needle across a rubric edit on stage.** Editing *weights* (e.g. a threshold slider) is fine and principled.
- Fan-out is intra-request **width**, not corpus density (one state per request; corpus scale = `Modal.map` over small payloads).
- Fan-out does **not** evaluate a decision tree — questions never see each other's answers.
- Calibration ≠ correctness. At 0.9 it's wrong 10% of the time *by design*, and it's calibrated on *their* distribution.
- **Don't say "it can't hallucinate" on stage.** Schema-safety is a decoder constraint, not a world constraint. TypeSafe publish their own weakness list; a judge may have read it.

**Access (verify before Saturday — this is go/no-go):** TypeSafe console is **waitlist-gated**. OpenRouter is the only realistic same-day path: `typesafe/jev-1.13` (alias `~typesafe/jev-latest`), base `https://openrouter.ai/api/v1`, **32K context**. `pip install typesafe-sdk` (0.7.0). Official agent skill at `docs.typesafe.ai/agent-skill.md` drops into Claude Code.

**Don't quote 40–200×** — TypeSafe's own evals, scored by *agreement with other models*, not ground truth. Defensible number: the independent Every.to test — ~25× faster, ~580× cheaper, missed 1 defect of 7. Also: Browser Use's `jev-ultrafast` got only **25% end-to-end** (9.5s → 7.1s) because the browser became the bottleneck — but **1,092 → 101 protocol calls**, which is the real result and pure fan-out.

**Reported weak spot:** Jev does notably worse on **invoice-processing-style tasks** and trails top comparators on aggregate workflow scores. That is uncomfortably close to Breaker's domain. **Test real judgements from the actual domain in hour one.**

## Standing advice that survived all three rounds

- **The idea is ~20% of P(win).** Binding constraints are who you team with at 09:35, whether the demo runs at 20:02, and how much was pre-built. Baseline P(first) ≈7%, →12–18% with a clean rehearsed demo.
- **Arrive with the skeleton built** — world sim, typed registry, `/reset`, working Modal deploy, all credentials redeemed. The cold-teammate analysis found **3–4.5 of 8.5 hours** otherwise vanish into Modal/Pydantic-AI first-contact friction. (The Jev ecosystem's SDKs/MCP servers/CLIs cut some of this.)
- **Target grand prize, lock a partner prize as the floor.** Partner prizes are softer competition — most teams bolt sponsor tech on shallowly.
- **Two big readings, not eleven rows.** The only fixes that survive stage nerves are baked into the render.
- **Design so no single model call can sink you.** Aggregate/statistical wows have built-in insurance.
- **Pitch the system, not the model.** "We used Jev!" is the graveyard.
- **Show a ~0.5 you refuse to trust** — otherwise you've demoed softmax theatre, not calibration.
- If the team is a dumpster fire at 11:00, join a stronger one or skip opt-in and spend the evening on sponsor conversations. Don't die on an idea.

## Open questions for the next session

1. **Confirm the event date** and ask organisers whether **pre-existing code is allowed** — this materially changes strategy (last user message was about reusing open-source repos as a base; the line drawn was: fork the plumbing and credit it, build the differentiated layer yourself).
2. **Verify an OpenRouter key actually hits `typesafe/jev-1.13`.** Go/no-go for anything Jev-based.
3. **Decide:** Breaker re-pitched around expected-loss + Modal fleet, vs. something in the unclaimed robotics space, vs. falling back to the revised Unwind spec (which needs no new model).
4. If Breaker proceeds: rewrite `FINAL-BUILD-SPEC.md` around the new framing (hour-by-hour + demo script), which was offered and not yet done.

## Tooling notes (saves rediscovery)

- **`codex` MCP server fails** (`CONNECTION_CLOSED`). Use the `codex` CLI: `codex exec -m gpt-5.6-sol --skip-git-repo-check -s read-only "<prompt>"`. Models `gpt-5.6-sol` / `gpt-5.6-terra` work; **astra is blocked on ChatGPT accounts** ("not supported when using Codex with a ChatGPT account").
- **Astra exists as `opencode/gpt-6-astra`** but the opencode **zen** route has **zero balance**. Top-up: the workspace billing page linked in opencode's error. Muse/GLM/Gemini via `opencode/*` hit the same wall — use `opencode-go/*` instead (that route has separate billing and works).
- **GLM** returned empty on 5.3 and 5.2; only **5.1** produced output.
- **Cursor** (`agent -p --mode ask --model <m> --trust "<prompt>"`) works for `cursor-grok-4.6-high|xhigh`, `kimi-k3-max`, `gemini-3.7-flash-high`.
- **`timeout` is not installed** on this Mac (no coreutils).
- X.com blocks WebFetch (HTTP 402) — use search or the browser tools.
- Long agent replies get **truncated in the idle notification**. Have agents write to a file and reply "written" instead.

## Suggested skills

- **`handoff`** — to re-compact at the end of the next session.
- **`artifact-design`** / **`dataviz`** — if building the Breaker UI (the two-big-readings render, the expected-loss display). Note the user's standing instruction: **never publish Artifacts unless explicitly asked** — files on disk, give the path.
- **`claude-api`** — before writing any Gemini/LLM integration code; don't answer model questions from memory.
- **`diagnose`** — if the Jev integration misbehaves during the build.
- **`tdd`** — only if the repo already has a test runner; the user's global rules forbid introducing tooling a repo doesn't have.
- The **TypeSafe official agent skill** (`docs.typesafe.ai/agent-skill.md`) — install before building with Jev.

## User preferences that apply (from global CLAUDE.md)

- **No Artifacts unless explicitly asked.** Deliver files on disk + the path. Don't render docs into chat.
- No emojis in PRs/commits; no `Co-Authored-By: Claude`; no `[Claude Code]`.
- No spec/plan/design docs committed to repos, and don't scaffold tooling a repo doesn't already have. (This directory is **not a git repo**, so the docs here are fine as workspace notes.)
- Copy-paste text (Slack/email/PR bodies): **one continuous line per paragraph**, never hard-wrapped.
- Panel conventions: "decide with agents" = 1 Sonnet + 1 Opus + 3 Codex; "panel review", "deep panel", "grand panel" have specific fixed compositions — see global CLAUDE.md. Codex panel prompts must **inline the full diff/context**, never "review my branch".
