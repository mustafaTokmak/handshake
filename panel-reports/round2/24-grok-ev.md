**Verdict: do not build Unwind as written.** It underperforms a smaller staging-fork on P(first), and its “sponsor fit” is mis-scored.

---

**1. Strongest case it is wrong**

Unwind spends the whole day on the *wrong half* of Conduct’s objection, then lies about the result.

Enterprises do not grant write access because rollback exists. They grant it when the agent never touches prod: a fork, a preview, a merge. Unwind builds disaster recovery for a world that is a JSON dict. The stage line (“the thing that makes that safe”) is a claim the architecture cannot support. A Pydantic or Conduct engineer will ask about the webhook, the bank, the CRM trigger. The only answer is “our ledger knows,” which is a puppet theatre.

Two load-bearing claims are false:

- **Pydantic does not make undo correct.** It checks that `create_contact(...)` is well-typed, not that it restores *the* contact, money, or causal graph. Semantic inversion, dependency order, and field-level conflicts are three distributed-systems problems. The 13:00–14:30 “Undo Brain” will collapse into hand-written compensators with Gemini narrating. The inverse synthesiser is theatre.
- **“Residual delta 0 of 12” contradicts the wow.** You preserve a human edit and you cannot unsend email. Residual vs the pre-incident snapshot is *not* zero unless you cook the metric. The board going green is the moment a technical judge stops believing you.

The plan also violates its own rationale. “Ambition correlates negatively with winning,” then: two agents, five serial Unwind stages, six tools, GitHub, Modal fork, conflict, irreversible, residual, Logfire tab, live judge-edit. That is not a conservative 8.5h demo. It is SIEGE-level surface area with a worse visual.

Uniqueness is not an argument. A unique demo the room cannot parse loses to a crowded demo the room can. Modal is used as a host, not as fan-out — the weakest possible Modal story in a room where Modal is judging.

---

**2. Most likely failure**

**13:30, inverse synthesis against the live registry.**

First Gemini Pro call emits an inverse that fails validation (`charge` is not a tool; `create_contact` is missing fields; deleted IDs come back as new IDs). The World lane already froze JSON at 11:00. Undo Brain adds `compensate_*` tools. Two registries. Actor still calls the originals. Until ~15:00 they are reconciling shapes.

**UI owner has nothing real until then.** At 15:30 they wire the table to a mocked plan fixture. The live path never fully reconnects.

Dress rehearsal **16:40**: Undo kicks **five serial Pro calls**, 50–90s on venue wifi. Script budget for the wow is 40s. They freeze the fixture plan. On stage they either play canned (Q&A kill: “was that live?”) or run live and the table does not match the board.

The 25s actor fallback does not save this. The *undo* is the part that is slow and non-deterministic, and it has no equivalent hard rule.

---

**3. Legibility at demo #12**

**The typed table does not land. The sentence might.**

A tired judge will not hold 14 mutations, two customer names, a live edit, three row types, a residual fraction, a git revert, and “the undo is undoable.” Fourteen streaming rows are noise. “0 of 12” requires memory of the 12. Conflict vs irreversible look like two yellow rows.

What survives without explanation: red board → “Undo” → green board. That is a traffic light, not a product. SIEGE’s tiles are higher-contrast by construction.

The live judge-edit is negative EV: awkward, slow, they may refuse or edit a field you do not key on. Cut it.

To make Unwind parse, you need a **frozen left pane (before) vs live right pane (after)** the entire 3 minutes, three objects max (customer, £4,200, email). That visual is not in the plan. Without it, Unwind is a clever paragraph attached to a spreadsheet.

---

**4. SIEGE was not wrongly rejected *as specified***

The 200-attacker / 5–15% lottery is a real trap. All-green and all-red both die in Q&A. Correctly killed.

The *redirect* was wrong. Calibration is engineerable: one planted, realistic composition bug with a locked exploit test before noon; 12–24 typed attack lanes for the visual; patch from a catalog; rerun. Call it a benchmark, not a discovery. “Red-teaming is a known shape” only kills you if you demo prompt-injection chat. A live exploit → patch → green regression is still the most legible 3 minutes in this sponsor set (DeepMind safety, Modal `map`, Pydantic contracts).

SIEGE-as-written: correctly dropped.  
SIEGE-as-seeded-eval: better grand-prize vehicle than Unwind-as-written. Crowding is a real discount, not a fatal one.

---

**5. Highest-leverage change**

**Delete inverse synthesis.** Tools declare compensators (or you do not undo at all). Gemini drafts the retraction sentence, nothing else.

Spend the recovered hours on a 3-object before/after split, not a 9-row table. Never claim residual 0. Pre-seed the human edit; do not crowd-source it from a judge.

If you take that seriously, you no longer have Unwind. You have a fork.

---

**6. BUILD SOMETHING ELSE — SHADOW: the agent only writes to a Modal-forked world; a human merges or discards.**

Same story as Unwind (“write access, made safe”), none of the inversion, residual, conflict, or five-stage LLM. Left pane = prod. Right pane = night run. One button.

---

## Independent EV (idea = 20% of P(win); ~14 demos, 1 grand)

I am not using the panel’s 12–18% as a target. Rebuilt from `P(first) ≈ P(works) × P(understood) × P(picked | those)`. Typical team ≈ `0.55 × 0.60 × 0.21 ≈ 7%`.

| | **P(demo works)** | **P(understood, 3 min, #12)** | **P(picked \| both)** | **P(first)** | **P(a partner prize)** |
|---|--:|--:|--:|--:|--:|
| Unwind as written | **0.55** (0.40 live-as-scripted; 0.75 if they actually fall back) | **0.45** | 0.22 | **5%** | **0.24** |
| SIEGE as written (200, stochastic) | **0.42** | **0.78** | 0.16 | **5%** | **0.12** |
| SIEGE seeded / “Canary” | **0.78** | **0.80** | 0.24 | **15%** | **0.20** |
| SHADOW (fork–diff–merge) | **0.80** | **0.82** | 0.25 | **16%** | **0.24** |
| Smaller-than-SHADOW “just ship a copilot” | 0.85 | 0.70 | 0.10 | **6%** | 0.10 |
| Do not optimise for prize (network, founder’s idea) | 0.70 | 0.55 | 0.10 | **4%** | 0.08 |

**Why those demo numbers:** Unwind has good *crash* fallbacks and a bad *live undo* path; five serial Pro calls plus a fake-world consistency problem. SIEGE-written is a calibration lottery plus swarm latency. Seeded SIEGE and SHADOW are one deterministic loop and a split screen.

**Partner prize ≠ grand.** Unwind’s one-liner is the best Conduct sentence in the room, so partner EV stays high even when grand EV does not. That is also a trap: Pydantic’s actual standard is *ship to production*. A Salesforce-shaped dict with `/reset` is the opposite. Expect a Pydantic judge to be colder than the panel assumed. Modal will not love a single-world host; they will love fan-out (seeded SIEGE) or “fork is the product” (SHADOW).

**Non-prize (relative, 0–100):**

| | Hire conversation | Investor remembers Monday | Repo still alive in 90 days | Net of “heads-down all day” |
|---|--:|--:|--:|--:|
| Unwind | 70 if it works, 40 if canned | **85** (best line) | 55 | −25 |
| SIEGE written | 55 (DeepMind/Modal) | 35 | 20 | −25 |
| SIEGE seeded | 60 | 45 | 40 | −15 |
| SHADOW | **75** (you finish ~17:00 and can talk) | 80 | 60 | **−5** |
| Network-max | 80 | 25 | 10 | 0 |

Rough prize-equivalent: grand = 100, partner = 25, “life” = the non-prize column.

- Unwind: `5 + 6 + 55` ≈ **66**, with fat left tail if the table fails to parse  
- SIEGE written: `5 + 3 + 25` ≈ **33**  
- SIEGE seeded: `15 + 5 + 45` ≈ **65**  
- SHADOW: `16 + 6 + 70` ≈ **92**  
- Network-max: `4 + 2 + 80` ≈ **86**

SHADOW wins joint EV. Network-max wins if you already have a company and do not need the trophy. Unwind and seeded SIEGE are close on *prize* EV; Unwind is a worse grand-prize bet and a better slogan.

**Third option with better EV than both as written:** SHADOW (smaller, more certain, same insight). Second: do not maximise P(first) — form the strongest team at 09:35, ship *their* thin sponsor-stack demo, spend 18:00–20:45 on Conduct/Pydantic/DeepMind people. That beats Unwind on career EV; it loses if you specifically want a trophy.

**Do not build Unwind as specified. Do not build 200-agent SIEGE.** If you refuse SHADOW, build **seeded SIEGE** (one planted exploit, parallel typed attacks, patch, re-verify) — not rollback.
