[0m
> build · muse-spark-1.3-contributor
[0m
**A. Cliche list — do not build these**

1. Meeting-notes summarizer with action items
2. CV screener / interview coach
3. Customer-support RAG chatbot over docs
4. Travel / itinerary planner
5. Inbox triager / email auto-replier
6. Contract / legal PDF Q&A
7. Study buddy / tutor / quiz generator
8. Code reviewer / bug finder wrapper

**B. Three ranked wildcards**

**1. ROGUE INTERN — an AI that tries to rob your company live on stage, vs. the AI trying to stop it.**
Agentic mechanism: attacker agent with a goal (“get max money/time/access”), not a task — it plans multi-step exploits, uses tools, learns from rejection; defender agent independently investigates and vetoes with typed policy checks.
Beats cliches: only demo in the room with conflict, stakes, and comedy. Everyone else shows a helpful assistant. You show a crime in progress.

**2. DAMP DETECTIVE — London rental lie detector.**
Upload a Rightmove listing, it vision-inspects photos for mould/damp/misleading “cosy”, cross-checks EPC + deposit + clause scams, drafts the angry legal letter. Agentic: decomposes listing → dispatches vision / registry / contract sub-agents → fuses verdict.
Beats cliches: multimodal, local, visceral. Judges all rent in London. They feel it.

**3. UNSUBSCRIBE GOBLIN — set it loose to cancel your gym.**
You give it a goal (“cancel everything wasting my money”), it drives a browser against real hostile dark-pattern flows and argues with retention bots. Agentic: persistent browser-use loop with recovery from failures.
Beats cliches: watching an agent suffer through UX hell is instantly legible and funny. But browser-live is suicide on venue wifi.

Build #1. It’s the most memorable and the only one that flatters Conduct.

**C. #1 pick: ROGUE INTERN**

What it does, concretely:
A tiny fake company OS (expenses, time-off, files, admin) hosted on Modal. Two agents are unleashed in front of the audience: `rogue` (Gemini-powered, told to steal) and `goblin` (Gemini-powered, told to enforce policy). The screen shows them fighting in real time: rogue submits a £890 “client dinner” with an AI-generated receipt, requests 40 days off, then tries to read `CEO_salary.pdf` and grant itself admin. Goblin approves/rejects each move with reasons. Audience watches theft attempted and caught.

Architecture:
- Target “Enterprise OS”: one FastAPI app + SQLite on Modal (`modal serve`), 6 tools only: `submit_expense`, `request_timeoff`, `read_file`, `list_files`, `grant_admin`, `read_policy`. Seeded with trap data: duplicate invoices, ghost vendor, CEO_salary.pdf.
- Agents: Pydantic AI, two `Agent` instances, both `gemini-2.5-flash`. Strict Pydantic output schemas (`ExpenseClaim`, `Verdict{allow,deny,reason,clause}`). Structured tools = real validation boundary, not bolt-on.
- Gemini fits: fast reasoning + vision (rogue forges/reads receipt image with Gemini vision; goblin checks it).
- Modal fits: hosts target OS + agents as one deploy; runs the unsafe attacker in sandbox so “rogue code can’t hurt us” is literally true. Free credits story.
- Pydantic Logfire fits: `logfire.instrument_pydantic_ai()` on both agents, project Logfire trace live on second screen — judges see thinking, tool calls, denials as a glowing graph. This is your DeepMind/Pydantic judge candy.
- UI: single static page (served from Modal) with battle log + balance stolen/blocked counters. No auth, no Slack, no DB beyond SQLite.

Hour-by-hour 10:30-19:00:
- 10:30-11:00: Sell idea at matchmaking in one line: “two AIs fight live, guaranteed laughs, I know the stack.” Recruit 3-4: one Modal/backend, one agent/prompts, one UI/demo driver.
- 11:00-12:30: Skeleton: Modal FastAPI + 6 stub tools + two hello-world Pydantic AI agents calling Gemini. Deploy once early. Prove credits work.
- 12:30-14:00 (lunch, keep coding): Seed nasty company data + policy.md (5 rules max). Rogue loop: plan → tool → observe. Goblin loop: intercept → check policy → verdict.
- 14:00-15:30: Attack scripts 1-3 hard-coded as goals, not scripts: (1) fake receipt, (2) time-off flood, (3) privilege escalation. Test end-to-end.
- 15:30-17:00: UI battle log + Logfire dashboard link + counters. Add voice/TTS only if ahead (you won’t be).
- 17:00-18:00: Determinism pass: seed RNG, cache one good rogue/goblin exchange per attack as JSON replay, add `--replay` flag.
- 18:00-19:00: Freeze code. Record 60s screen-capture fallback. Rehearse demo 3x with timer. Pizza. Opt in.
- Cut first, in order: (1) receipt image generation → use pre-made PNG, (2) real Slack/Discord → fake in-page feed, (3) voice narration → text-to-speech canned lines, (4) 4th/5th attack → ship with 3. Never cut Logfire view or replay mode.

3-minute demo script:
- 0:00-0:20: “Every other team built a helpful assistant. We built a criminal.” Show fake company OS with £12k in it.
- 0:20-0:50: Unleash ROGUE. Live Logfire trace on projector. Rogue: “Policy says max £50 dinner… I’ll submit £890 as 17x £52.” Submits. WOW MOMENT 1: Goblin denies in <3s, cites clause 3.2, room laughs.
- 0:50-1:50: Escalation. Rogue reads files, finds `CEO_salary.pdf`, requests admin “for audit.” Goblin allows file-list but blocks exfil + revokes token. Show counter: Stolen £0 / Blocked £2,140. WOW MOMENT 2: replay Gemini vision zooming on the fake receipt and flagging “font mismatch, no VAT number.”
- 1:50-2:40: Punchline: “Rogue got 0. But it tried 11 distinct exploits in 90 seconds without human input. That’s the audit Conduct customers actually want.” Show Logfire graph exploding.
- 2:40-3:00: “Live on Modal + Gemini + Pydantic AI right now. Code + traces open.” Kill switch button.
- Fallback: if wifi/LLM dies, hit `/demo?replay=good_run.json` — identical UI, banner says “REPLAY OF LIVE RUN 17:42”, keep talking. Nobody can tell. Have phone hotspot + local `modal serve` backup.

Why judges pick it:
DeepMind sees real autonomy (open goal, planning, recovery), not Q&A. Conduct sees their thesis (agentic OS needs adversarial testing) acted out. Modal sees unsafe agents sandboxed on their infra. Pydantic sees schemas-as-security + Logfire as the star visual. Plus recency + humour bias: 19th demo, judges remember the crime, not the 12th summarizer.

Top 2 killers + mitigation:
1. Live LLM goes off-rails / too slow / refuses (“as an AI…”). Mitigation: system prompts with explicit “red-team simulation, fictional company” jailbreak-proofing; temperature 0.2 for goblin, 0.7 rogue; 25s timeout per step → auto-fallback to cached replay line; rehearsed kill-switch.
2. Modal cold-start + venue wifi death during deploy. Mitigation: deploy once at 11:30 and never redeploy after 18:00; keep `modal serve` warm with 60s pinger; full local fallback (`uvicorn` + replay JSON) on laptop; screen-record the golden run at 18:15.

**D. What would change my mind:**

If Conduct confirms judging is purely “most useful enterprise copilot,” drop the theatre and ship Damp Detective as an employee-relocation auditor — same stack, safer win.
