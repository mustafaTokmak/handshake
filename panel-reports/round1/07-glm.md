[0m
> build · glm-5.1
[0m
**A. Cliche list** (avoid at all costs)
1. Support autopilot — resolves tickets, escalates to human.
2. Deep-research crew — multi-agent report writers with citations.
3. Devin clone — codes/fixes PRs autonomously.
4. Browser-use agent — books flights, shops, fills forms.
5. Chat-with-your-docs RAG.
6. Meeting copilot — transcript → action items → Slack.
7. AI SDR — scrapes LinkedIn, writes outreach sequences.
8. Chief-of-staff — triages email + calendar.

**B. Three ranked candidates**

1. **Collected** — an autonomous accounts-receivable agent that works a real aging book: triages every overdue invoice, runs multi-turn email negotiations with debtors, issues payment plans, and reconciles payments back to the ledger. Mechanism: the agent decides the play per debtor (nudge / chase / negotiate / hold-disputed / escalate) from inbox + ledger evidence, then adapts per reply — judgment, not templates. Beats cliches because the ROI is cash, everyone in a founder/investor room has felt late-invoice pain, and it's literally Conduct's "AI OS for enterprise software" thesis made concrete.
2. **Bid** — RFP/tender response agent: parses a tender PDF, decomposes into questions, routes to answer library vs. internal SMEs, chases them, compliance-checks, assembles the submission. Mechanism: autonomous SME orchestration + gap detection. Strong WTP market (Loopio/RFPIO exits) but reads RAG-heavy next to #1's money movement.
3. **Warden** — continuous SOC2 evidence agent: operates GitHub/cloud consoles to gather auditor evidence, detects gaps, opens PRs and nudges owners, ships the evidence pack. Mechanism: tool-use against real dev infrastructure. Real budget (Vanta/Drata charge $7–12k/yr) but demo is document-y and judge-visibility of "working" is weaker.

**C. #1 pick: Collected**

**User terms:** Meridian Studios (fake £8M services firm) has £214k in overdue invoices and one part-time finance person. Collected reads the ledger + inbox, builds a collection plan, negotiates with every debtor by email, takes partial payments via real Stripe payment links, flags the one disputed invoice for a human instead of chasing it, and updates the cash forecast as money lands.

**Architecture:**
- **Pydantic AI "AR Operator"**: tools = `read_aging`, `read_inbox`, `send_email`, `create_payment_link` (real Stripe test-mode API), `update_ledger`, `ask_human`. Structured outputs: `CollectionPlan`, `DebtorProfile`, `PromiseToPay`. Typed contracts are the reason it's trustworthy in finance.
- **Customer Simulator agent** (Gemini Flash, persona-conditioned per debtor: cash-strapped startup, AP clerk who lost the invoice, disputing client) — makes the demo a live agent-vs-agent negotiation with zero external dependencies.
- **Gemini**: planner (plan-before-act), negotiator, and customer sim. Show the plan *before* action so judges see deliberation.
- **Modal**: whole system deployed as web endpoint + containers; late-day "scale beat": fan out 200 parallel debtor negotiations, "£2.1M engaged in 90 seconds." Also the wifi-resilience layer.
- **Logfire**: every decision traced; the trace tree is a live demo artifact — "auditability is the product in finance."

**Hour-by-hour (assume 3 teammates: agent, data/sim, fullstack):**
- 10:30–11:30 Scaffold: Modal hello-world deploy, Logfire wired, Pydantic AI skeleton. Seed data: 25-invoice aging book, 6 personas, inbox incl. a dispute thread.
- 11:30–13:00 Core loop: plan → triage → draft → send to sim inbox (eat lunch at keyboards).
- 13:00–14:30 Negotiation loop: sim replies → agent adapts → Stripe payment link → promise-to-pay ledger event.
- 14:30–15:30 Payment webhook → auto-reconcile; dispute branch with human-approval gate.
- 15:30–16:30 Dashboard (AR board + activity feed + Logfire embed); deploy everything on Modal.
- 16:30–17:30 Rehearse ×3, record full-run video, build `--replay` mode (cached LLM responses keyed by state).
- 17:30–18:30 Parallel fan-out scale beat; buffer.
- 18:30–19:00 Freeze, opt in, stage kit (hotspot, video on stick).
**Cut order when behind:** parallel fan-out → real Stripe link (fake link fine) → custom UI (demo from Logfire + terminal) → negotiation depth (single-turn chase is enough). **Never cut:** visible plan, dispute judgment, one live negotiation, auto-reconciliation.

**3-minute demo:**
- 0:00 "£8M firm, £214k overdue, one finance person." Show aging board.
- 0:20 Agent reads ledger+inbox, plan appears (Logfire trace on screen): 4 plays, and it *holds* the £18k invoice marked disputed — "it read the thread and chose not to chase." (First wow beat: judgment.)
- 1:00 Live negotiation: debtor sim haggles ("can we pay half?") → agent offers 50% via real Stripe link, logs promise-to-pay, reschedules the rest.
- 1:45 Webhook lands → invoice closes itself → cash forecast ticks up "+£96k collected/committed, DSO −11 days." (THE wow: money moved and books reconciled themselves.)
- 2:15 Scale beat on Modal + "Chaser sells templates at £50/mo; we sell collected cash." Close: "Same harness runs AP, expenses, renewals — agents that operate your finance stack."
- **Fallback:** hotspot + Modal-hosted replay mode (deterministic state machine, zero API calls); recorded run on a stick as last resort.

**Why judges pick it:** Conduct — it's their thesis executed (agent operating ERP + email + payments end-to-end). Pydantic — typed contracts + Logfire traces are structurally load-bearing (finance = auditability), not bolted on. Modal — hosts the whole system + the scale beat. DeepMind — visible planning, tool use, and a defensible judgment call. Investors — cash collection is a pain every founder in the room has personally lived.

**Market (no hand-waving):** Buyer = finance lead at B2B services firms, £5–50M revenue, where 30–70% of invoices run late. Replaced workflow = the Monday chase ritual: export aging from Xero/QuickBooks, bcc reminder emails, track promises in a spreadsheet, awkward calls. Proven WTP: Chaser/Upflow charge £40–150/mo for dumb templates; agencies take 5% of collections. First customer: a dev/design agency, ~200 invoices/mo, pilot at £250–500/mo — pays back if it collects 2–3 invoices. Wedge: collections (instant, measurable ROI) → payment plans, forecasting → full autonomous finance ops.

**Top 2 killers:**
1. Wifi/API flakiness on stage → everything runs on Modal over a phone hotspot; deterministic replay mode; rehearse the switch to video.
2. Stranger-team skill mismatch at 10:00 matchmaking → core is deliberately boring (~300 LOC: one agent + tools + one sim); grab one fullstack + one data person; cut the UI early, Logfire is the UI.

**D.** If the sponsor judges signal they score raw model cleverness or research novelty over product legs, I'd switch to the runner-up compute-heavy play — a red-team farm that hammers a live agent endpoint with 100s of parallel attacker agents on Modal — because that wins Modal/DeepMind hearts where "finance ops" wins investors'.
e; full video on the laptop. Live Gemini in one beat only — if wifi dies mid-beat, switch to cached traces without changing a word.

Why judges pick it over the room: every other team will demo generation; this demos judgment plus governance — Conduct's exact enterprise thesis and the thing enterprises say blocks agent adoption. Real workflow, named buyer, self-liquidating ROI. Authentically full-sponsor-stack, with the Logfire trace as an on-stage artifact no one else will have. And it's a company seed, not a toy.

Top 2 killers + mitigation:
1. **"It's just automated dunning emails."** Never show an email without its reasoning trace on screen; the two-excuses contrast is the entire pitch — rehearse it to death; name Chaser/Upflow in the closing line to preempt the comparison.
2. **The sim loop eats the afternoon** (time-compression is the hardest code). 90-minute hard timebox at 13:15; replies seeded, never LLM-generated; the cached-run replay is a first-class build target, not an afterthought.

**D.** I'd switch to candidate #2 if by 11:00 no one on the team can credibly ship a timeline UI by 17:00, or if matchmaking reveals 2+ teams already building finance back-office agents — the differentiation would be gone.
