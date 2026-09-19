### A. Cliché List (Ideas at least 10 teams will pitch)
1. **The SDR / Inbound Lead Qualifier:** Scrapes LinkedIn/websites and writes personalized outreach emails.
2. **The "RAG on Company Docs" Support Bot:** Chatbot querying Zendesk/Notion with semantic search.
3. **The Automated PR / Code Review Agent:** Lints GitHub diffs, comments stylistic suggestions, and opens a trivial PR.
4. **The Meeting-to-Jira Pipeline:** Transcribes audio and creates ticket backlogs in Linear/Jira.
5. **The Autonomous Web Research Agent:** Multi-agent search loop that compiles a markdown market research report.
6. **The Financial Analyst / SEC 10-K Summarizer:** Pulls ticker data and SEC filings to produce stock sentiment summaries.
7. **The Resume Screener / HR Matcher:** Scores resumes against job descriptions using structured output.

---

### B. Three Ranked Candidate Ideas

#### 1. RetroAgent: Zero-API Legacy Enterprise Automation from Screen Recording
* **What it is:** Turn a raw 10-minute Loom/screen recording of a worker navigating legacy enterprise UIs (SAP, Oracle, bespoke portals) into a fully deployed, self-healing automated worker API.
* **Agentic Mechanism:** Gemini consumes the raw video natively, synthesizes the latent business logic and visual UI transitions into an executable state machine, writes browser automation code, runs it in an isolated sandbox, visually observes errors, and self-corrects until verified.
* **Why it beats the cliches:** It attacks the multi-billion-dollar enterprise legacy software problem (Conduct's exact thesis) using native video understanding that is impossible without Gemini’s 1M+ token multimodal context window.

#### 2. CrossCheck: 1M-Token Multimodal Forensic Fraud & Collusion Hunter
* **What it is:** Ingests an entire quarter of heterogeneous enterprise artifacts (1,000 PDFs, raw transaction ledgers, recorded supplier negotiation calls, CCTV snapshots) to autonomously trace multi-hop compliance fraud.
* **Agentic Mechanism:** Pydantic AI agent builds a cross-modal anomaly graph, uses deep thinking budgets to hypothesize collusion vectors, generates and runs sandboxed verification scripts on ledgers, and produces courtroom-grade forensic proof.
* **Why it beats the cliches:** It exercises DeepMind's 1M–2M context window on messy multimodal data rather than toy RAG chunks.

#### 3. AirTrafficOps: Real-Time Multimodal Emergency Dispatch Co-Pilot
* **What it is:** A live audio/visual triage console that monitors concurrent CCTV/telemetry feeds and assists dispatchers during multi-site industrial or transit incidents.
* **Agentic Mechanism:** Runs live stream reasoning over multiple feeds, plans resource allocation across municipal APIs, verifies constraints (hazard zones, crew fatigue), and dispatches autonomous API actions.
* **Why it beats the cliches:** Uses real-time multimodal reasoning for mission-critical operations instead of generic asynchronous chat.

---

### C. #1 Pick: RetroAgent (Zero-API Enterprise Automation from Raw Video)

```
[Employee Loom Video (MP4)] 
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ Gemini 2.0 Flash / Pro (Native Multimodal Video Engine)  │
│ - Ingests raw video (no OCR/transcription pipeline)      │
│ - Uses Thinking Budget to infer unstated edge cases     │
│ - Outputs structured state graph: (Actions, Selectors)   │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Pydantic AI Orchestrator                                 │
│ - Enforces strict Schema validation (Pydantic models)   │
│ - Synthesizes deterministic Playwright / Python code    │
│ - Instruments end-to-end telemetry via Logfire          │
└──────────────────────────┬──────────────────────────────┘
                           │ Dispatches Sandbox
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Modal Serverless Execution Runtime                      │
│ - Spins up parallel headless browser containers         │
│ - Runs automation against target legacy portal mock     │
│ - Captures runtime failure screenshots/DOM logs         │
└──────────────────────────┬──────────────────────────────┘
                           │ Failure Feedback Loop
                           ▼
┌─────────────────────────────────────────────────────────┐
│ Autonomous Self-Healing Loop                            │
│ - Gemini inspects failure screenshot + DOM log          │
│ - Pydantic AI patches script & re-tests on Modal        │
│ - Logfire visualizes real-time repair tree              │
└─────────────────────────────────────────────────────────┘
```

#### 1. What it does (User Terms)
An enterprise operator uploads a standard screen recording of themselves doing a tedious, repetitive task across legacy web apps with no APIs (e.g., cross-referencing invoice PDFs with an internal billing portal and updating record statuses). Within 60 seconds, **RetroAgent** analyzes the video, generates a reliable browser automation worker, executes it in a cloud sandbox, self-heals broken UI selectors in real time, and provides a production-ready webhook endpoint that replaces the manual work.

#### 2. Architecture & Sponsor Alignment
* **Google DeepMind (Gemini 2.0 Flash/Pro):** 
  * *Native Video Understanding:* Directly uploads raw `.mp4` into Gemini (no manual OCR or ffmpeg frame slicing). Gemini tracks cursor coordinates, input values, and visual state transitions natively.
  * *Thinking Budget:* Used to infer business logic exceptions (e.g., *"If status is 'Pending', click re-verify; if 'Flagged', escalate"*).
* **Pydantic AI & Logfire:** 
  * *Pydantic AI:* Defines the deterministic state machine (`WorkflowStep`, `ActionType`, `DOMSelector`, `AssertionSchema`).
  * *Logfire:* Displayed live on screen during the demo, showing real-time agent execution traces, latency, model reasoning steps, and the self-healing retry loop.
* **Modal:** 
  * Serverless execution engine running containerized headless Playwright instances. Executes the generated code on demand with sub-second cold starts.
* **Conduct Enterprise Angle:** 
  * Directly solves the core enterprise operating system problem: bridging un-API-able legacy software into modern autonomous workflows.

---

#### 3. Hour-by-Hour Build Plan (10:30 – 19:00)

* **10:30–11:30 | Core Contracts & Mock Setup (Parallelized)**
  * *Dev 1:* Build a local mock "Legacy ERP Portal" (raw HTML/CSS with intentional edge cases, e.g., unexpected modal pop-ups, dynamic IDs). Record a clean 3-minute Loom video of the manual task.
  * *Dev 2:* Set up Gemini 2.0 Video Ingestion pipeline + Pydantic schema (`WorkflowGraph`).
  * *Dev 3:* Set up Modal Playwright worker template + Logfire instrumentation.
* **11:30–13:30 | Video-to-Workflow Synthesis**
  * Prompt Gemini with video + system prompt to output `WorkflowGraph` with strict Pydantic validation.
  * Build the Playwright code generator from the validated schema.
* **13:30–15:30 | Modal Execution & Self-Healing Loop**
  * Wire Modal container to run generated Playwright scripts against the mock portal.
  * Implement the recovery loop: when Playwright fails, capture screenshot + DOM snapshot $\rightarrow$ feed back to Gemini Flash $\rightarrow$ re-patch script.
* **15:30–17:00 | Frontend & Logfire Observability**
  * Minimal UI: Video upload on left, live Modal browser stream in center, Logfire live trace view on right.
* **17:00–18:00 | End-to-End Stress Testing & Fallbacks**
  * Hardcode deterministic fallback caches for the exact demo video. Record backup screen capture of the end-to-end run.
* **18:00–19:00 | Rehearsal & Polish**
  * Dry-run the 3-minute pitch 5 times with team.

**What to cut first if behind schedule:**
1. *Cut full video upload UI:* Hardcode the pre-recorded video path in the backend and show a clickable thumbnail.
2. *Cut dynamic mock site:* Test against a static mock page with 3 predictable steps instead of 6.
3. *Cut multi-step self-healing:* Allow the agent to fix a single broken selector rather than handling complex structural layout shifts.

---

#### 4. The 3-Minute Demo Script

* **[0:00–0:30] The Hook & Enterprise Pain:**
  * *"Enterprise automation is stuck because 80% of back-office software has no APIs. Companies pay millions for manual copy-pasting or brittle RPA that breaks on every UI update."*
* **[0:30–1:00] Ingesting Raw Video (DeepMind Native Multimodal):**
  * Show a 2-minute raw video of a user doing messy invoice reconciliation on an ancient UI.
  * Click *"Synthesize Worker"*. Show Gemini parsing visual state changes and generating the Pydantic workflow model in 10 seconds.
* **[1:00–2:15] The WOW Moment (Live Sandboxed Execution & Autonomous Self-Healing):**
  * Modal launches a headless browser. Live stream shows the bot executing the steps automatically.
  * **The Twist:** The mock site deliberately throws a new dynamic anti-bot banner / altered button ID that was *not* in the training video.
  * The execution halts. Logfire shows: `[ERROR: SelectorNotFound] -> [Pydantic AI: Triggering Gemini Self-Heal]`.
  * Gemini inspects the live failure screenshot from Modal, detects the new UI layout, rewrites the selector, and completes the workflow. Logfire traces turn bright green.
* **[2:15–2:45] Instant Deployment:**
  * Show the generated Modal webhook endpoint: *"This 10-minute manual task is now a permanent serverless API."*
* **[2:45–3:00] Closing & Sponsor Tech Recap:**
  * Summarize: Gemini 2.0 native video + Pydantic AI structured validation + Modal instant browser containers + Logfire live observability.

**Pre-recorded Fallback Plan:**
* Pre-deploy a verified Modal worker instance pointing to a hosted replica of the mock site. If live inference lags over venue Wi-Fi, toggle the demo UI switch to *"Replay Cached Run"* (which executes the real Modal container against pre-computed Gemini outputs while keeping all browser automation live).

---

#### 5. Why Judges Pick It Over the Room
1. **DeepMind judges** see true native video tokens and reasoning budgets being used for something structurally impossible with text-only LLMs or naive screenshot sampling.
2. **Conduct judges** see an immediate solution to the enterprise AI integration bottleneck.
3. **Modal judges** see their infrastructure running isolated, bursty browser compute that delivers high performance.
4. **Pydantic judges** see Logfire as the hero of the live stage demo, proving how type validation and observability make agents production-grade.

#### 6. Top 2 Failure Risks & Mitigations
1. **Risk 1: Video Token Processing Latency (Gemini File API timeout on venue Wi-Fi).**
   * *Mitigation:* Pre-upload the demo video to Google AI Studio / Gemini File API before the presentation; pass the existing `file_uri` directly in the live call to skip upload bandwidth entirely.
2. **Risk 2: Playwright flaky timing / selector race conditions on stage.**
   * *Mitigation:* Use explicit Playwright network-idle assertions (`page.wait_for_load_state('networkidle')`) and configure the target mock app with zero external network dependencies (hosted locally or on the same Modal network).

---

### D. What Would Change My Mind

I would change my mind if your assembled team consists exclusively of deep systems/quant developers with zero web automation/frontend experience, in which case you should pivot to **Idea #2 (CrossCheck)** for a pure data-and-ledger backend engine.
