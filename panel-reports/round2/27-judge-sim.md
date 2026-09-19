# 27 — COLD JUDGE SIMULATION (Opus)

Role: simulate the judge, not analyse the project. 20:36, demo #12 of 12, awards at 20:45.
Two demos tonight were genuinely good, six blurred together, three broke. Feet hurt. One beer at 19:10.

---

## COLD JUDGE #1 — Modal infra engineer, minute by minute

**20:35:40.** Team eleven is unplugging. My lower back hurts. I have written eleven rows in my notes app; four of them say "?". The beer was at 19:10 and it's doing nothing good for me now. I check: awards at 20:45. Nine minutes after this one and I can sit down somewhere that isn't this stool.

**20:36:00 — "Every team tonight gave an agent write access to something. We built the thing that makes that safe."**

Okay. That's a real sentence. Most people open with "so, we noticed that..." — this one opened with a claim about *me*. Small alertness bump. I did actually give an agent write access to a repo last Tuesday and it force-pushed. I write "undo?" in my notes.

Mild suspicion in parallel: that line is the kind of thing that promises more than three minutes can hold. I've been burned twice tonight already by a great opening sentence attached to a curl command.

**20:36:20 — the actor agent starts running. Presenter goes silent.**

Screen fills with tool calls. Green text scrolling.

And — I'm out. Not dramatically, just: this is the sixth time tonight I have watched text scroll down a dark rectangle while someone stands next to it. My eyes go to the shape of it rather than the content. I read maybe four of the fourteen lines. `crm.update_field`. Something about a refund. An email thing. Some of the panel is turning red, which I register as "the demo is working as intended" rather than as information.

Somewhere around the twenty-second mark I look at my phone. Not proud of it. Slack, nothing, back up.

**This is the part the team will never believe: I did not encode the mess.** I know a mess happened. I could not have told you a single field that changed. If the payload of this demo requires me to remember what the world looked like at 20:36:15, the payload is already lost, and it's 20:36:50.

**20:36:55 — "Can someone from the judging table come edit one field?"**

Oh. Oh, that's — okay, I'm back. Fully back. The Pydantic guy next to me goes up. The whole room turns to watch him instead of the screen, which is fine, because he's about to become part of the demo. He types something into a field labelled with a customer name. Twelve seconds, maybe fifteen.

Two things happen in my head at once. First: **they don't know what he typed.** Whatever comes next is not pre-baked, and I now have a reason to watch the screen that I did not have thirty seconds ago. Second, slightly cynical: *they'd better have a reason for this.*

This is the single best thing they've done and it is happening at the fifty-five-second mark, which is late.

**20:37:10 — "Undo."**

A table renders. Fast — fast enough that I clock the latency as real rather than pre-rendered. Good.

And now the actual test, which is: **can I read it?** I'm ten, eleven feet back. The table has — I count the block, I don't read it — about a dozen rows and four or five columns. Monospace. It is *dense*. My first act is not reading; my first act is waiting to be told where to look. That's what a tired person does with a table: they do not parse it, they wait for the pointer.

The presenter gives me the pointer. "Nine of these reverse automatically. Look at these two."

Thank you. Genuinely — thank you. If they had read the table to me I'd have been gone again.

**20:37:25 — the CONFLICT row.**

"A human edited this field forty seconds ago. We are not going to clobber their change."

That lands. It lands *hard*, and here is the mechanism, because it's not what I'd have predicted: **I did not have to reconstruct anything.** I didn't need to remember the before-state. I watched a man from the judging table type into a box ninety seconds ago, and now a machine is refusing to overwrite him, by name, with a timestamp. That's not a counterfactual. That's a thing I saw happen, followed by the correct response to it.

What I feel is not "clever." What I feel is *recognition*. I have been paged at 03:40 for exactly this — a reconciliation job that reverted a field an on-call human had hand-patched forty minutes earlier, and we spent the morning working out which value was real. My note says, verbatim: `refuses to clobber human edit — correct`.

**20:37:35 — the IRREVERSIBLE row.**

"The email was delivered. We cannot unsend it. We've drafted a retraction and routed it to a named human."

This is the moment I start trusting them, and it's worth being precise about why. At demo twelve, my default posture is *waiting for the lie*. Every system tonight that claimed complete success made me hunt for what it was hiding. A row that says **"I can't do this one"** disarms that instinct for about four seconds' worth of stage time. It's the cheapest credibility in the building and they bought it.

It also, quietly, answers the question I hadn't consciously formed yet — "is this just a diff-and-replay toy" — no, they thought about the boundary. Note: `knows what it can't undo. good.`

**20:37:45 — Modal dry-run, residual delta.**

Now I'm the Modal guy so this is my bit. "Forked the world into a sandbox, replayed the inverse plan there first, residual delta zero of twelve."

Two reactions, half a second apart.

First: that is *the right architecture*. Dry-run the inverse before you commit it. I would ship that.

Second, and it doesn't go away for the rest of the night: **did you actually fork anything, or did you deepcopy a dict and call it a fork?** The screen says something happened. I can't see a container ID, a sandbox handle, a cold-start, anything that looks like our platform rather than like a function call. If they'd flashed one line — sandbox spun, 900ms, here's the handle — I'd have zero doubt. As it is, it's my one open question, and it's a question about *my own product*, which means I will absolutely raise it in the huddle.

Also, small thing, and I want to be honest that it registered: it said zero of twelve, and I'm fairly sure the run earlier said fourteen calls, and the table looked like eleven rows. I can't reconcile those numbers from where I'm sitting and I don't try. It doesn't cost them much. It costs them a little — it reads as "assembled in a hurry" in a way I can't articulate but do feel.

**20:37:55 — board goes green, repo shows a revert commit.**

Red-to-green is the only part of this demo my *eyes* enjoy, and it's over in three seconds. The GitHub revert is the strongest beat in the entire thing and it gets about four seconds: that is a real commit, in a real repo, that a real agent wrote and a real agent reverted. That is the one place the demo touches the actual world. I'd have traded the whole Logfire section for fifteen more seconds on that.

**20:38:15 — Logfire tab. "The undo is itself an agent run, so the undo is undoable."**

I hear the words. I follow them about seventy percent. There's a nod-and-smile reflex that fires, but I'm not going to pretend I *felt* anything. It's a recursion joke, and recursion jokes are for hour two of a conference, not minute one-hundred-and-thirty-eight of a Saturday. The Logfire trace itself looks tidy. I register "they instrumented it," which is worth something, and I register that this is the Pydantic sponsor beat, not mine.

If I'm being brutal: these twenty-five seconds are the weakest in the demo and they sit exactly where the demo should be landing the plane. I'd cut the punchline and spend it on the two rows that actually worked.

**20:38:35 — close. Applause. It's over and I got all of it except the first thirty-five seconds.**

Overall, sitting on my stool: that's the third-best thing I've seen tonight, possibly the second. Not because it was the most impressive engineering — it isn't, the swarm team's parallelism was more impressive — but because it's the only demo tonight where I thought "I have had this exact outage."

---

## COLD JUDGE #2 — Pydantic engineer (same demo, what differs)

I'm the one who went up and edited the field, so I'm compromised on attention — I watched the whole back half sharply because I was waiting to see my own input come back.

What I notice that the Modal guy doesn't:

- **The inverse plan is validated against the same tool registry.** They say it in one clause, in passing, at about 1:20, and it goes by in two seconds. That is the single most interesting engineering claim in the demo and it is delivered as a subordinate clause. A structurally invalid undo *cannot be emitted* — that's the whole argument for typed tools, that's literally our tagline, and they buried it. I catch it because it's my job to catch it. Nobody else in the room heard it.
- Conversely, I'm the person most likely to ask the deflating question: **the model wrote the inverse plan, and I'm being shown that it's well-typed, not that it's correct.** Well-typed nonsense is still nonsense. The residual-delta diff is their answer to that and it's a good answer, but it flew past in eight seconds and I only reconstructed it afterwards.
- Logfire tab: I like it more than he does, obviously. But I've seen four Logfire tabs tonight and they're starting to look like a tax teams pay to sponsors. The undo-is-undoable line is the only one that earned the tab, and it earned it conceptually, not visually.

My note: `only team tonight where the types were doing load-bearing work rather than decorating a function signature.`

---

## COLD JUDGE #3 — DeepMind researcher (same demo, what differs)

I get it at 1:05 and I'm slightly bored by 1:50, and I want to be honest about why, because it's not fair but it's what happened.

- The conflict row and the irreversible row are **authored constraints.** They wrote the world. They decided email is irreversible. They decided six tools exist. So what I am watching is a system correctly handling the cases its own authors installed for it to handle. I don't think that's cheating — you have to simulate *something* in eight hours — but it caps how impressed I can be. The judge-edit is the only genuinely unscripted input in the run, and one unscripted input is enough to prove the loop is live but not enough to prove it generalises.
- The intellectually interesting object here is the **inverse synthesiser** — a model reading an effect ledger and producing compensating actions under a type constraint. That's a real problem. The demo shows me its *output* and never shows me its *difficulty*. I never see it fail, never see an ambiguous case, never see it say "I have two candidate inverses." So I can't tell if it's an LLM doing something hard or a lookup table with a model-shaped wrapper over it.
- Against that: the framing sentence is correct and it is about the actual thing that is wrong with 2026. Everyone is shipping write-access agents and nobody has a story for the morning after. That earns real points with me, separately from the engineering.

My note: `right problem. can't tell how much of the hard part is real. would ask in Q&A if there were Q&A.`

---

## THE HUDDLE — 20:58, three of us, standing, awards in seven minutes

> **Organiser:** okay, going round — which one had the undo thing?
>
> **Me (Modal):** twelve. Last one. The one where Tomas went up and edited the record and then it refused to overwrite him.
>
> **Pydantic:** that's me, I'm Tomas.
>
> **Me:** right, sorry. Yeah — that one. Rollback for agents.
>
> **DeepMind:** the enterprise simulator.
>
> **Me:** the point was, it showed you a plan before it did anything, and two rows in the plan were "I'm not touching this, a human edited it" and "this email is already sent, I can't unsend it, here's a draft retraction for a human." That second one is the bit I keep thinking about. Nobody else tonight told us what they *couldn't* do.
>
> **DeepMind:** it's a saga pattern with a model writing the compensations.
>
> **Me:** sure, but nobody's shipped it for agent tool calls and every one of us has needed it. I've had that 3am page.
>
> **DeepMind:** my hesitation is the world is theirs. They wrote the mess and they wrote the undo. The one real integration was the GitHub revert and it got four seconds.
>
> **Me:** which is fair. My version of that is I don't know if the "fork the world into a Modal sandbox" was a real sandbox or a dict copy. It said residual delta zero of twelve. I'd want to see the sandbox.
>
> **Pydantic:** it was real, they mentioned — actually I don't know either.
>
> **Me:** right. So we're both assuming.
>
> **Organiser:** versus the swarm one?
>
> **Me:** the swarm looked better. Two hundred tiles going red is a better photograph than a table. But I sat there for ninety seconds not knowing whether the target they were attacking was hard or a paper bag, and I still don't know, and I asked and got an answer I didn't follow.
>
> **DeepMind:** the score went 62 to 94. I have no idea what the units are.
>
> **Me:** exactly. With the undo one I know exactly what I'd get if I installed it. It's smaller and I believe all of it.
>
> **Pydantic:** the typed-inverse thing is genuinely the right idea, and it's the only team tonight where the schemas were load-bearing.
>
> **Organiser:** so top three?
>
> **Me:** the undo one's in it for me. Top two or three. I wouldn't fight for it as grand prize over — what was three, the voice one? — but for our prize, it's the one.

**What that recall test actually showed:**
- It was recalled **instantly**, by a story ("Tomas edited the record and it refused to overwrite him"), not by a feature name.
- The two remembered beats were the two **admissions of limitation**, not the nine successes.
- Its weakness in the huddle was an **unverifiable sponsor claim** (was the Modal fork real?), not the concept.
- The DeepMind objection — "the world is theirs" — was raised, was fair, and was survivable. It keeps Unwind off the top step, not off the podium.

---

## SIEGE — same night, same judge, briefly

- **0:00** — "we built two hundred attacker agents." Number is sticky. I'm awake.
- **0:20** — grid of tiles appears, starts flickering red. Best-looking thing tonight. I'd photograph it.
- **0:40** — I understand the entire concept and I have not had to hold anything in my head. Zero cognitive load. This is real, and it is Unwind's structural disadvantage stated in one line.
- **1:00** — first adversarial thought arrives, right on schedule: *how hard is the target?* Once that thought arrives it does not leave, and everything after it is filtered through it.
- **1:30** — auto-patch, re-verify, tiles go green. Nice. Still thinking about the target.
- **2:00** — score 62 → 94. I don't know what 62 means. I don't know what 94 means. I don't know what a breach is in their definition. The number is doing emotional work it hasn't earned, and I resent it slightly, because I'm tired and I can't check it.
- **2:40** — close. Applause, louder than Unwind's.
- **Huddle:** "the swarm one looked incredible — do we believe it?" Nobody can answer. **An unanswerable question at 21:00 among tired engineers resolves as no.**

SIEGE wins the room and loses the huddle. Unwind loses the room and wins the huddle. Which matters depends entirely on whether the prize is decided by applause or by three exhausted people standing in a corner — and it's the corner.

---

## THE ADDED VARIANT — PRECHECK / Airlock / SHADOW, run through the same tired judge

Three round-2 agents independently converged on moving the intervention **before** the write: preview the proposed writes, show blast radius, human stamps or discards; or the agent only ever writes to a Modal-forked copy and a human merges. Same slogan, first-order, no counterfactual.

Simulated at demo #12, cold.

**0:00** — "we built the thing that makes agent write access safe." Same opening. Still good.
**0:20** — agent proposes a batch of writes. A panel fills with proposed changes and a blast-radius summary: 12 fields, 2 contacts, GBP 4,200, 1 email, 1 commit. **Nothing has happened yet.**
**0:35 — I understand it completely.** No counterfactual, no memory load, no re-entry cost. On the pure legibility axis the agents are right and it beats Unwind cleanly.
**0:40 — and here is the problem, and it arrives four seconds after comprehension: *so it's a confirmation dialog.*** That thought is not hostile, it is *categorising*. I have approved a diff in Cursor, in Claude Code, in Copilot, in Terraform plan, in every CI pipeline I have ever touched. `terraform plan` is thirteen years old and it is literally this: proposed writes, blast radius, apply or discard. My brain files this demo into an existing folder within half a second of understanding it, and **once something is filed, it stops competing.**

This is the thing the legibility argument misses. **At demo #12 my problem is not comprehension, it is discrimination.** Six demos blurred together tonight precisely *because* I understood all of them instantly and none of them landed anywhere new. Instant legibility and instant categorisation are the same event. Unwind's slightly slower comprehension is also what makes it unfilable: I have never seen an undo table before, so I have nowhere to put it except "new."

**1:00 — the dramatic problem.** Nothing goes wrong. Nothing is red. There is no disaster and therefore no rescue. I am being shown an absence — a bad thing that did not happen. A smoke detector that does not go off is not a demo. Unwind has a fire and a fire extinguisher and I can see both; PRECHECK has a fire *warning* and my agreement that fires are bad. At 20:36 the story with a middle wins.

**1:20 — the Q&A thought I would actually ask, and it's the killer for PRECHECK/Airlock specifically.** If a human has to stamp every write, **you have deleted the agent.** Approval queues die of alert fatigue within a week — every enterprise person in this room has watched one die. Conduct's whole pitch is enterprise AI operating systems; their customers' complaint is *exactly* "we ended up with a human approving 400 things a day and turned it off." So the co-host with the hardest sales objection hears PRECHECK and thinks: that's the thing we already tried. Whereas Unwind's pitch is "let it run unattended overnight, because the morning after is recoverable" — which is the actual unlock, and the reason you would buy anything here at all.

**SHADOW is the strongest of the three and deserves separate credit.** Left pane prod, right pane night-run, one merge button — that is a *visual*, not a table, and it is legible at ten feet where Unwind's monospace grid is not. And the Modal fork stops being a dry-run flourish and becomes the product itself, which as the Modal judge I would like a great deal more than a dry-run I can't verify.

But two things break it under the same cold eye:

1. **"So it's a git branch for my CRM."** Filed. Same instant-categorisation death. Staging environments exist.
2. **The merge button is Unwind's conflict problem wearing a hat.** If the night-run touched 12 fields and a human touched 2 of them during the night, "one button" is a lie — and it is a lie that any judge who has ever merged anything spots in about two seconds. So SHADOW either hand-waves the merge (and dies in the huddle) or it builds the classifier and conflict detection anyway, which is **the same build, minus the drama, minus the irreversible-email beat** (in a shadow world the email was never sent, so the best credibility beat in the whole plan evaporates).

**The free steal.** The variant's genuinely valuable contribution is not architectural, it's verbal, and it costs nothing: **Unwind's 1:05–1:45 already IS a preview-before-write moment.** The undo plan is a proposed set of writes, with a blast radius, shown before anything executes, gated by a human. The team just never says so. Put the variant's exact sentence into Unwind's script at 1:05 — *"nothing has happened yet; this is what we propose to do, and this is what we refuse to do"* — and Unwind gets PRECHECK's first-order legibility **and** keeps the fire. That is a one-line script change, not a pivot.

**Verdict on the variant: worse, and worse for a reason that inverts the argument for it.** Its advantage (instant comprehension) is inseparable from its fatal flaw (instant categorisation into `terraform plan` / confirm dialog / staging branch). Unwind's cost (thirty-five seconds of dead setup) is fixable with a script edit; PRECHECK's cost (being a familiar shape) is not fixable at all.

---

## THE SIX QUESTIONS

**1. The strongest argument the pick is wrong.**
Everything that makes Unwind impressive happens inside a world the team authored. They wrote the tools, they decided which one is irreversible, they wrote the mess and the undo. The DeepMind judge said it out loud in the huddle and neither of us could rebut it: the only surface where the system touches reality is the GitHub commit/revert — **and the cut order lists GitHub as the first thing to cut.** That cut order is therefore backwards under adversarial judging: it sheds the only evidence that this isn't a self-consistent toy, and keeps the beats a sufficiently cynical judge can read as stagecraft. A demo whose entire credibility rests on one real integration should defend that integration first, not cut it first.

**2. The single most likely failure, with the hour.**
**20:01, on stage: the judge-edit anti-canned move.** It is the best thing in the demo and it is the only moment where unvalidated human input generates the wow row live. Failure modes, all plausible: the judge edits a field the actor never touched (no overlap → **no CONFLICT row renders at all**, and the presenter is standing in front of a nine-row all-green table with thirty seconds of script that no longer applies); they type an empty string or paste something the Pydantic model rejects; they edit the wrong record; they take forty seconds instead of twelve and eat the Modal beat. Rehearsing three times with teammates does not test this, because teammates edit the correct field correctly.

Second most likely, and the one that *causes* the first: **15:30–16:30, the Modal sandbox fork.** Forking a live world into a real Modal sandbox and replaying a plan there is a container-lifecycle problem, not an app problem — serialisation, cold start, getting the diff back — and it will overrun into the 16:30–17:15 slot. That slot holds the two credibility beats the cut order says never to cut. Because Modal is a sponsor, sunk cost will defend the fork, and conflict detection will arrive untested at 18:20, thirty minutes before freeze. That is exactly how the 20:01 failure gets built.

**3. Is the 3-minute demo legible to a tired judge at demo #12?**
**Yes — but not by the mechanism the plan assumes, and the first thirty-five seconds are dead weight that nearly kill it.**

The fear is wrong in a specific way: **the CONFLICT row does not require a counterfactual.** I did not reconstruct the before-state. I watched a human type into a box ninety seconds earlier, then watched a machine refuse to overwrite him, by name, with a timestamp. That is a *witnessed event followed by a response* — the cheapest possible comprehension. Same for IRREVERSIBLE: "you can't unsend an email" needs no baseline; it is recognition, not reasoning. **Both wow beats survive a judge who was on his phone during the mess**, because the plan table re-states the mess as it reverses it. The wow is self-contained. That is the structural strength the round-1 panel never named.

What *does* fail: 0:20–0:55, thirty-five seconds of scrolling tool calls with the presenter silent, is the most fungible visual in the building — I'd seen it five times already and I left the room mentally. That is 20% of the budget spent on the one thing that cannot differentiate you, immediately before the beat that needs my attention most. And the plan table is a *text* wow: eleven rows of dense monospace at ten feet is a thing a tired person waits to be told about rather than reads. It survived only because the presenter said "nine are boring, look at these two." If the presenter reads the table under stage adrenaline, it dies.

The Logfire recursion punchline does not land on a tired person. It is a joke for hour two of a conference. The GitHub revert — the strongest credibility beat they own — gets four seconds.

**4. Was SIEGE wrongly rejected?**
No, and the huddle is why. SIEGE's problem isn't that it might come out all-green or all-red; it's that **its central claim is unverifiable in three minutes and the judge knows it's unverifiable within sixty seconds.** "62 → 94" is a number doing emotional work it hasn't earned, and a tired judge's response to an unearned number is not disbelief, it's *suspension* — and suspension at 20:58 with awards at 21:05 resolves as "we can't give it the prize, we don't know what we'd be rewarding." That's a losing state you cannot argue your way out of from the stage. Unwind's equivalent objection ("the world is theirs") is also real, but it is *bounded*: it caps the ceiling, it doesn't void the demo. SIEGE wins the applause, the photograph and the clip. It loses the corner where the decision is made. **Rejection upheld** — and the PRECHECK/Airlock/SHADOW family is a worse swap than SIEGE was, for the categorisation reason above.

**5. The single highest-leverage change.**
**Render the plan as two big rows plus one collapsed line — not eleven rows.** CONFLICT and IRREVERSIBLE at large type, each as one readable English sentence, and above them a single grey line: `9 other effects — auto-reversed`, expandable if anyone asks. Roughly twenty lines of UI. It converts the wow from "a dense table a tired man waits to be told about" into "two sentences legible from the back of the room," it removes the dependency on presenter discipline under adrenaline (**the only fixes that survive stage nerves are the ones baked into the render**), and it stops nine boring rows from diluting the two that carry the entire demo.

Three small things that must ride along, all near-free, all at the points where the demo actually dies:
- **(a)** Constrain the judge's edit to one pre-highlighted field — "change the account owner here, type anything" — and have the backend synthesise a conflict row if the edit doesn't overlap the effect set, so the row *cannot* fail to appear.
- **(b)** Cut the Logfire recursion punchline; spend those twenty seconds holding the GitHub revert on screen with the diff visible. It is the only non-toy surface — show it like you mean it, and **move it below Modal in the cut order** (cut Modal first, not GitHub).
- **(c)** Say the variant's sentence at 1:05: *"nothing has happened yet — this is what we propose to do, and this is what we refuse to do."* Free first-order legibility, no architecture change.

**6. Verdict.**
**BUILD UNWIND.** It was the only demo tonight where a judge thought "I have had this exact outage," and that sentence is what survives the walk to the corner at 20:58.
