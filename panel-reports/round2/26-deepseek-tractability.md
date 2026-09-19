[0m
> build · deepseek-v4.1-flash
[0m
## 1. Strongest case this pick is WRONG

The pick is optimized for the wrong failure mode. It is built to survive a demo that *doesn't crash*, but its mechanism is **self-referential** — you author the world, the snapshot, the ledger, the inverses, and the "verification." A passing dry-run is guaranteed if you didn't write a bug. So the thing you spent the day proving is "our code is internally consistent," and the thing you didn't prove is "this would ever help a real enterprise." The strongest case against: you're spending 8.5 hours to build a *demo that looks rigorous to a non-technical judge but is hollow to the exact sponsor engineers sitting in the room* — Pydantic literally sells "agents you'll actually ship," and Conduct sells "AI operating systems for enterprise software." Those are the people who will ask the three questions below. If the answers are thin, you converted your best differentiator ("we hit their exact tagline") into your sharpest liability.

## 2. Most likely single failure

**14:30–15:30, "Undo Brain" lane.** Two people discover that for 4 of 6 tools the inverse is a mechanical replay of the recorded `before` snapshot — no synthesis needed — and for the other 2 it's genuinely underdetermined. They then fork: either hardcode `TOOL → INVERSE` (fast, reliable, decorative) or try to make Gemini do real synthesis (interesting, unreliable). Given the whole reason you picked Unwind is *reliability*, they hardcode. It works. The demo runs. And on the 16:00 run-through nobody notices the agent is decorative until Q&A. This is a design landmine, not a crash — and it's invisible to your rehearsals.

## 3. The three questions, blunt

**(1) Inverse synthesis — yes, it collapses to a lookup table as specified.** You record `before/after` per Effect. The inverse is then computable with zero LLM: `restore(before)`. "Validated against the same registry" is also weaker than it sounds — validating a Pydantic model you constructed yourself is tautological type-checking of your own constructor, and validating an LLM-emitted plan against a tool registry is **Pydantic AI's default behavior you get for free by using the framework.** It is not a contribution; do not pitch it as one. The defensible non-mechanical work is *ordering*: reversing a compound sequence where the naive per-call reverse is invalid mid-sequence (delete-contact before un-enrolling it from a campaign violates an FK). That's real planning. Lean on it.

**(2) Classifier — decorative if classification is a property of the tool.** CRM-update reversible, email-send irreversible, billing-compensable is a `dict` lookup; Gemini adds nothing, and "what does the classifier do?" is answered with "it reads the tool name." It becomes *real* only if the class depends on **arguments and current state**: refund is reversible if unsettled, compensable if settled; message is reversible if unread, irreversible if reacted to; commit is reversible if unpushed, irreversible if merged+deployed. That is buildable, but it costs world-modeling hours you've already overbooked. As written: decorative.

**(3) Modal fork-and-replay proves nothing about safety.** You control subject and oracle. In a single-writer in-memory FastAPI state, "no concurrent writers" is a fact of your architecture, not a guarantee your system provides. Residual-delta-zero means your inverse functions match your forward functions — a unit test. What it *genuinely* buys, and your best honest line, is: **the ordered inverse plan executes in a disposable copy before it touches the real one**, which is real engineering practice and it catches dependency-ordering bugs before they hit the stage. Say exactly that. Never say "verified."

## 4–5. SIEGE and highest leverage

**SIEGE was rejected for the right reason (demo variance), not because it's a worse idea.** Its success metric is empirical — did the patch survive re-attack — which is genuinely non-self-referential and more intellectually honest than anything Unwind verifies. Unwind is the safer bet; don't tell yourself it's the better idea.

**Highest-leverage change:** make reversibility **call/state-dependent for at least two tools** (add settlement state to refund, read-state to messaging) and make the **CONFLICT row the spine of the demo**, not the "9 of 12 reversible." The conflict — human divergence between ledger and current state — is the only beat that is neither a mechanical diff replay nor a self-referential check, and it's the thing enterprises actually fear. Also make the retraction email the one *generative* inverse drafted live on stage; that single frame is what disproves "lookup table."

**Demo legibility:** the counterfactual is fine — they watched it go red, so red→green is a state change, not a hold. The killer is **dense typed table text on a projector at demo #12**. Cut the second-order punchline ("the undo is undoable") and "residual delta 0 of 12" — neither lands tired; icons + color + the presenter speaking only the CONFLICT and IRREVERSIBLE rows are what survive.

## 6. Verdict

**BUILD UNWIND — but reframed as an inverse *planner with human-divergence detection*, not "agentic inverse synthesis," and spend the saved time making one classifier axis and one inverse genuinely non-mechanical.** If the pitch says "validated against the registry," drop that line before a Pydantic engineer asks you what validation proves.
