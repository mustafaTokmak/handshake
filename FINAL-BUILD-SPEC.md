# UNWIND — final build spec (after round-2 red team)

Supersedes the recommendation in `IDEA-PANEL-VERDICT.md`. That file's panel table and cliché list still stand; its build plan and demo script are **replaced by this one**.

Round-2 raw reports: `…/scratchpad/round2/`

## The vote

Eight adversarial agents, each told to attack the round-1 pick:

| Agent | Role | Verdict |
|---|---|---|
| Codex gpt-5.6-sol | kill Unwind | **SOMETHING ELSE** — PRECHECK (preview writes, blast radius, human commit) |
| Codex gpt-5.6-terra | defend SIEGE | **SIEGE**, but seeded/deterministic, not a stochastic swarm |
| Grok 4.6 high | category-error hunt | **SOMETHING ELSE** — Airlock (refuse + rewrite before the write) |
| Grok 4.6 xhigh | independent EV | **SOMETHING ELSE** — SHADOW (fork–diff–merge). EV 92 vs Unwind 66 |
| Kimi K3 | base rates on scope | **UNWIND — the subset.** The panel quoted the ambition warning then spec'd an ambitious demo |
| DeepSeek v4.1 | tractability audit | **UNWIND**, reframed — drop the "inverse synthesis" claim |
| Claude Sonnet 5 | cold-teammate build test | **UNWIND**, conditional on a fluency triage |
| Claude Opus 5 | tired-judge simulation | **UNWIND** |

**4 Unwind / 3 preview-before-write / 1 SIEGE.** Verdict: **build Unwind, heavily revised.** The three defectors converged on a genuinely strong idea, and it was tested and rejected for a non-obvious reason — §2.

## 1. What round 2 broke

Four findings, each from an independent agent, each real:

**a. The "inverse synthesiser" is theatre.** You record `before`/`after` per effect, so the inverse is `restore(before)` — computable with zero LLM. DeepSeek, Codex-sol and Grok all landed on this independently. Worse, "validated against the same Pydantic tool registry" is Pydantic AI's *default behaviour that you get for free*, and validating a model you constructed yourself is tautological. **Do not pitch it as a contribution.** A Pydantic engineer will ask what the validation proves and the honest answer is "nothing."

**b. "Residual delta 0 of 12" is a logic bomb.** You cannot preserve a human edit *and* be unable to unsend an email *and* report zero residual, unless the denominator is cooked. Three agents caught it. It is the exact moment a technical judge stops believing you.

**c. The budget is off by 40-100%.** Codex-sol priced the build at 36-56 person-hours against ~25-30 effective. The cold-teammate found why: **3-4.5 of the 8.5 hours** go to Modal account/ASGI-wrapping/image-build friction, the Pydantic AI + Gemini agent API learning curve, and inventing what "effect ledger with causal parent" concretely means. The plan budgets zero for any of it.

**d. The cut order is backwards.** GitHub revert is the *only* surface where this system touches reality, and it was first to cut. The judge simulation caught this: a demo whose credibility rests on one real integration must defend that integration first.

## 2. Why not PRECHECK / Airlock / SHADOW

Three agents independently said: move the intervention *before* the write. Preview the proposed changes, show blast radius, human stamps or discards. Same slogan, first-order, no counterfactual to hold. Grok's EV model scored SHADOW at 92 against Unwind's 66.

It is a real idea and the judge simulation ran it cold. It loses, for a reason that inverts the argument for it:

> *"0:35 — I understand it completely. 0:40 — and here is the problem, arriving four seconds after comprehension: **so it's a confirmation dialog.** `terraform plan` is thirteen years old and it is literally this. My brain files this demo into an existing folder within half a second of understanding it, and once something is filed, it stops competing."*

**At demo #12 the judge's problem is discrimination, not comprehension.** Instant legibility and instant categorisation are the same event — six demos blurred together that night *because* they were understood instantly and landed nowhere new. Unwind's slightly slower comprehension is also what makes it unfilable.

Three more strikes: it shows an **absence** — a bad thing that did not happen, a smoke detector that does not go off, no fire and therefore no rescue. If a human stamps every write, **you have deleted the agent** — and approval-queue fatigue is precisely what Conduct's customers already tried and switched off. And SHADOW's one-button merge is Unwind's conflict problem wearing a hat: if the night-run touched 12 fields and a human touched 2, "one button" is a lie any judge spots in seconds — so SHADOW builds the same classifier and conflict detection anyway, minus the drama, and in a shadow world the email was never sent, so the best beat in the plan evaporates.

**Take the sentence, not the architecture.** Unwind's 1:05-1:45 *already is* a preview-before-write moment — a proposed set of writes, with blast radius, shown before anything executes, gated by a human. Say so: **"nothing has happened yet — this is what we propose to do, and this is what we refuse to do."** Free first-order legibility, one line of script, no pivot.

## 3. Why not SIEGE

Rejection upheld, but for a better reason than round 1 gave. Codex-terra and Kimi both showed the calibration risk *is* engineerable — plant one realistic composition flaw (a confused-deputy export path), lock a deterministic exploit test before noon, let the swarm supply breadth and the visual. So my round-1 reasoning was wrong.

The real problem is what the judge simulation found in the huddle: **SIEGE's central claim is unverifiable in three minutes, and the judge knows it is unverifiable within sixty seconds.** "62 → 94" is a number doing emotional work it has not earned. A tired judge's response to an unearned number is not disbelief, it is *suspension* — and suspension at 20:58 with awards at 21:05 resolves as "we can't reward it, we don't know what we'd be rewarding."

> *"The swarm one looked incredible — do we believe it?" Nobody can answer. An unanswerable question at 21:00 among tired engineers resolves as no.*

**SIEGE wins the room and loses the corner. Unwind loses the room and wins the corner. The prize is decided in the corner.**

## 4. The legibility fear was wrong

The main worry — that the audience must hold a counterfactual — does not survive simulation. The Modal judge was **on his phone** during the mess and the wow still landed:

> *"I did not reconstruct the before-state. I watched a human type into a box ninety seconds earlier, then watched a machine refuse to overwrite him, by name, with a timestamp. That is a witnessed event followed by a response — the cheapest possible comprehension."*

Both wow beats are self-contained. CONFLICT works because the judge *witnessed* the edit. IRREVERSIBLE works because "you can't unsend an email" needs no baseline — it is recognition, not reasoning. The plan table re-states the mess as it reverses it.

This also means **the judge-edit beat is load-bearing, not optional.** Grok wanted it cut as negative EV; the simulation shows it is the mechanism that makes the wow work at all. It is also the single most likely on-stage failure (§6), so it gets engineered, not cut.

What the huddle actually recalled, 20 minutes later: *"the one where Tomas went up and edited the record and then it refused to overwrite him."* Recalled instantly, by a **story**, not a feature — and the two remembered beats were **the two admissions of limitation**, not the nine successes.

## 5. The revised build

**Scope: the subset.** Four tools (CRM, Billing, Email, Files). Cut Calendar and Messaging.

**Script the actor.** *(Kimi — the highest-leverage change of round 2.)* A fixed, versioned scenario file: 14 calls, exact arguments. Gemini Flash generates only the reasoning *narration* around each call. This makes the plan table deterministic, makes the 13:00 fixture byte-identical to the live run so the fallback is seamless, and drops the live chain from 10 components to ~6. The Q&A answer is strong and true: **"Unwind operates on the ledger; it doesn't care who wrote the calls."**

**Delete inverse synthesis; declare compensators.** Each tool declares its compensator, precondition/version, reversibility class, and conflict-check fields. The agent classifies and explains; it does not invent inverses. Gemini drafts the retraction sentence — that one generative inverse, drafted live, is what disproves "lookup table."

**Make the classifier real.** As specified it is a dict lookup on tool name and Gemini is decorative. Make reversibility depend on **arguments and current state** for at least two tools: refund is reversible if unsettled, compensable if settled; message is reversible if unread, irreversible if read. That is the difference between a real reasoning task and "it reads the tool name."

**Modal: honest framing.** Fork-and-replay does not prove safety — you control subject and oracle, so residual-zero is a unit test. The true and still-good line: **"the ordered inverse plan executes in a disposable copy before it touches the real one."** Never say "verified." And **cut Modal before GitHub**, reversing the round-1 order.

**Never claim residual 0.** Say: *"2 restored, 1 preserved human change, 1 outstanding external consequence."*

### Revised hour-by-hour

| Time | Work |
|---|---|
| 10:30-10:45 | **Stack-fluency triage.** Ask outright: who has used Modal? Pydantic AI? Assign lanes by that answer, not by who volunteers. |
| 10:45-11:20 | **Forced parallel smoke tests before any feature code.** One person ships a literal one-endpoint Modal hello-world; another does a one-tool Pydantic AI + Gemini round trip. This converts "deploy before noon" from hope into evidence by 11:20 — and if either fails you invoke the cut order with 7 hours of runway instead of discovering it at 12:45 with none. |
| 11:20-12:30 | World sim (4 tools), typed registry with declared compensators, effect ledger, `/reset`. Deployed. |
| 12:30-13:00 | Scripted actor + canonical fixture. **Hard checkpoint: if the fixture does not exist at 13:00, start cutting. Do not negotiate.** |
| 13:00-14:30 | Classifier (state-dependent on 2 tools) + planner + conflict detection. |
| 14:30-15:45 | UI: two panes. Object board + the two-row plan. |
| 15:45-16:45 | The two credibility beats: irreversible email → live-drafted retraction; conflict row. |
| 16:45-17:30 | GitHub revert, with the diff visible. This is the only non-toy surface — build it, don't cut it. |
| 17:30-18:00 | Modal fork dry-run **only if ahead**. Otherwise local snapshot copy, same code. |
| 18:00-18:30 | Record fallback. **Freeze code.** |
| 18:30-19:00 | Rehearse 3× on venue wifi. Opt in. |

**Cut order (revised):** Modal fork → GitHub → conflict detection → down to 3 tools.
**Never cut:** the irreversible-email beat, the scripted actor, `/reset`, the recorded fallback.

### Revised demo

- **0:00-0:20** — "Every team tonight gave an agent write access to something. We built the thing that makes that safe."
- **0:20-0:50** — Run the scripted actor. **Narrate it — do not stand in silence.** Thirty-five seconds of scrolling tool calls with a silent presenter is the most fungible visual in the building; the judge left the room mentally and it is 20% of your budget spent on the one thing that cannot differentiate you. Instead: *"that's a refund. that's a deleted customer. that's an email nobody can unsend."* Board renders **objects** — `Acme Ltd — active, £12k ARR` — not events, so "before" is a picture, not a memory.
- **0:50-1:05** — **"Someone from the judging table, change the account owner here — type anything."** Pre-highlight the exact field. Backend synthesises a conflict row if the edit doesn't overlap the effect set, so **the row cannot fail to appear.**
- **1:05-1:45 — THE WOW.** *"Nothing has happened yet. This is what we propose to do, and this is what we refuse to do."* Then **two big rows, not eleven** — CONFLICT and IRREVERSIBLE in large type, each one readable English sentence, above a single collapsed grey line: `9 other effects — auto-reversed`. Roughly twenty lines of UI, and it is the highest-leverage change in the whole spec: it converts the wow from a dense table a tired man waits to be told about into two sentences legible from the back of the room. **The only fixes that survive stage nerves are the ones baked into the render** — do not rely on the presenter pointing at the right rows under adrenaline.
- **1:45-2:15** — Execute. Board goes green except what you honestly could not restore. Say the honest tally, never "residual 0."
- **2:15-2:40** — **GitHub revert, diff on screen, held.** Your only non-toy surface — show it like you mean it. **Cut the "undo is undoable" punchline**; it is a joke for hour two of a conference and it does not land on a tired person.
- **2:40-3:00** — Close.

**Fallbacks:** the scripted actor makes the fixture byte-identical to the live run, so the 25-second switch is genuinely seamless; 90-second recording one click away; one slide showing the two-row plan.

## 6. The two ways it still dies

**20:01 — the judge edit.** The best thing in the demo and the only moment where unvalidated human input generates the wow live. They edit a field the actor never touched → no CONFLICT row renders and you are standing in front of an all-green table with thirty seconds of script that no longer applies. Or they paste something the model rejects, or take forty seconds. *Rehearsing with teammates does not test this, because teammates edit the correct field correctly.* **Mitigation: pre-highlight one field, constrain the input, and have the backend guarantee the row.**

**15:45-17:30 — sunk cost defends the Modal fork.** Forking a live world into a real sandbox is a container-lifecycle problem, not an app problem, and it overruns into the slot holding your two credibility beats. Because Modal is a sponsor, the team will defend it, and conflict detection arrives untested at 18:20. **That is exactly how the 20:01 failure gets built.** Mitigation: Modal fork is now first on the cut list and gated on being ahead at 17:30.

## 7. Still true from round 1

The idea is ~20% of P(win). **Arrive Saturday with the skeleton already built** — world sim, typed registry, `/reset`, a working Modal deploy, all four sets of credentials redeemed. The cold-teammate analysis makes this non-optional: 3-4.5 hours of the day otherwise disappear into first-contact friction with the sponsor stack, and that is the difference between shipping this and shipping a chatbot.

Target the grand prize, but **lock the Pydantic partner prize as your floor** — Logfire is consumed by the product rather than merely emitted, and per the huddle this was *"the only team tonight where the schemas were load-bearing."*

And Grok's standing advice: if the team is a dumpster fire at 11:00, join a stronger one or skip opt-in and spend the evening on sponsor conversations. Do not die on an idea.
