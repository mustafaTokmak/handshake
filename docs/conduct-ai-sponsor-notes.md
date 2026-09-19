# Conduct AI (conduct.ai) - Sponsor Research Notes

Researched: Sep 19, 2026

## Who they are

- **Conduct AI Ltd.** - "AI Operating System for enterprise software"
- London-based, founded 2024, ~30 people
- CEO/Co-founder: Jan-Philipp Haas; CPO: Philipp Hoefer
- May 2026: named **SAP Strategic AI Partner** for SAP Cloud ERP transformation (on track to become SAP Endorsed App on SAP Store); exhibited at SAP Sapphire Orlando
- Customers: DHL, Daimler Truck, Heidelberg Materials, Fraport (DAX40-scale)
- Links: https://conduct.ai | LinkedIn /conduct-ai/ | X @ConductAI

## Product: three pillars

1. **Understand**
   - Reads custom code + configuration of enterprise systems (SAP first)
   - Dependency mapping, downstream impact analysis, process inference
   - Always-current auto-documentation; "capture institutional knowledge"
   - Example capability: "identify custom programs relevant for goods movement and create a process diagram" -> returns function modules, BAPIs used, call volumes

2. **Operate**
   - Full change lifecycle: business request -> structured technical task -> plan -> build -> test -> deploy
   - Identifies affected processes/objects/dependencies before dev starts
   - Change Request / Workflow UI with implementation plans

3. **Transform**
   - S/4HANA migration tooling: clean core grading, fit-gap analysis, template delta resolution, structured code refactoring
   - RISE with SAP journey acceleration

## Integrations (their build surface)

| Category | Available | Coming |
|---|---|---|
| System of record | SAP (deep: config + custom code), Salesforce, Workday | Oracle |
| IT ops toolchain | Jira, Confluence, ServiceNow (claimed) | - |
| SAP ecosystem | SAP Signavio, SAP LeanIX | - |
| SAP tooling | Cloud ALM (native integration) | - |

## Headline metrics (marketing claims)

- 80% faster manual system analysis
- 50% faster feature delivery
- 30% lower S/4HANA migration cost
- 83% faster S/4HANA migration planning
- 48h onboarding/setup

## Hackathon relevance (key findings)

- **No public API, SDK, or MCP.** Enterprise product; sits behind auth on customer landscapes. You cannot self-serve access.
- Their headline-sponsored hack was **UK AI Agent Hack Ep5** (Imperial College London, Jun 28 - Jul 4 2026, with fetch.ai/Microsoft/OpenAI):
  - Track was generic agentic-AI (Fetch.ai ASI:One + Agentverse), NOT Conduct tooling
  - Conduct role: headline sponsor, mentors, judges, internship interview opportunities
  - Prize pool ~$33k total; Cantor8 dinner prize GBP 7,500; winning teams invited to exclusive Sept meet-up
  - Judging: functionality/tech (25%), sponsor-tech use (25%), innovation (20%), real-world impact (20%), UX/presentation (10%)

## What we can actually use from Conduct at the hack

1. **Product shape as inspiration** - the "context engine" pattern: deeply read a system -> map dependencies -> auto-document -> plan -> build -> test -> deploy. Agentic enterprise-system workflows.
2. **Their integration map as our build surface** - Jira, Confluence, Salesforce, Workday, Signavio/LeanIX all have public APIs. Ideas that hit their lanes without needing their product:
   - change request -> dependency impact analysis -> ticket -> docs update
   - clean-core scoring / fit-gap agent on custom code
   - system-intelligence chat over Confluence+Jira+repo data
3. **On-site access - must ask at their booth/track on day 1:**
   - "Do you have a sandbox/demo tenant, demo data, or an MCP for the hack?"
   - Ask for a challenge brief if they have a named sponsor track
   - CPO Philipp Hoefer and account leads (awood@, tdreusicke@, schampion@conduct.ai) take 1:1s

## Scoring strategy (based on their hack judging)

- Meaningful tool execution / agent-to-agent orchestration beats thin chatbot wrappers
- Reliability + error handling on failed tool calls gets bonus
- Realistic "operates after the hack" persistence gets bonus
- Demo must run end-to-end without custom frontend
