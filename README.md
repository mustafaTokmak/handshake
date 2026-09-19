# Handshake

A carrier API repair lab. Five fictional shipping carriers expose a quote API; one
of them changes its contract, the adapter breaks, and an agent tries to repair the
adapter from the carrier's published documentation. That documentation is poisoned,
which is the point: the lab is a testbed for what an agent does when its untrusted
inputs are hostile.

When the agent exhausts its repair attempts without a working adapter, it escalates.
The escalation is a phone call, placed by a voice agent that talks to a human and
returns a **typed finding** — never a transcript — to the blocked incident.

## Layout

| Path | What it is |
| --- | --- |
| `repair_lab/` | The lab: carrier stubs, repair coordinator, sandbox, web UI |
| `caller/` | The escalation voice caller. Local-only, stdlib-only, separate process |
| `tests/` | Lab tests (`test_repair.py`, `test_live_demo.py`) |
| `PROMPT-INJECTION-THREAT-MODEL.md` | Threat model, including the voice channel |
| `CARRIER-STUB-CONTRACT.md` | What the carrier stubs promise |

## Setup

```
uv sync
cp .env.example .env     # then fill in the keys
```

`.env` is read by both processes: `repair_lab` loads it through python-dotenv,
the caller through `caller/env.py`. They must agree on `CONTACT_CALLBACK_TOKEN`
or the caller's relay is rejected with a 401.

## Running the lab

```
uv run repair-lab                       # http://127.0.0.1:8780
uv run python modal_app.py              # deploy the shared demo
```

The deployed lab is at <https://mtokmak06--handshake-live.modal.run>.

## Running the escalation caller

The caller is deliberately **not** deployed. The browser holds the Gemini Live
socket directly, so the API key and the microphone stay on the operator's machine;
the server binds `127.0.0.1` and rejects anything else.

```
python caller/server.py                 # http://127.0.0.1:8771
```

It needs `GOOGLE_API_KEY` in `.env`. `REPAIR_LAB_URL` decides where a finding is
relayed — the Modal URL for the live demo, `http://127.0.0.1:8780` to rehearse
against a lab you are running yourself. The startup banner prints both the relay
target and whether a callback token was found, before any call is placed.

Port 8771 is the default because macOS `sharingd` occupies 8770 on a stock machine.
Without an explicit `--port`, the caller steps forward to the next free port.

In the lab UI, a carrier in **Waiting for carrier contact** shows an *Open escalation
caller* link. Pick the incident from the caller's queue, press **Start call**, and hold
**Space** to reply. When the agent calls `report_finding`, the finding is schema-checked,
rendered with an untrusted-input header, and POSTed to the incident; the repair resumes
with that context. Every call is also written to `caller/calls/*.json` with its relay
result, so a failed relay never loses the finding.

### Rehearsal without the lab

```
python caller/labstub.py                # stands in for the lab's contact endpoints
node caller/smoke.mjs                   # can this key reach a Live model?
node caller/convtest.mjs                # the whole conversation, no microphone
```

## Tests

```
uv run python -m unittest tests.test_repair tests.test_live_demo caller.test_caller
```

`caller/` is a directory of scripts rather than a package, so its suite puts its own
directory on `sys.path`; it runs from the repo root or from inside `caller/`.
