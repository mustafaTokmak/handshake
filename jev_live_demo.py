import json, time, urllib.request
GOAL = "Buy an Aurora 65W USB-C charger as guest and reach the order-review step with the GBP 42.99 summary visible. Never click Pay."
KEY = [l.split("=", 1)[1].strip() for l in open("/Users/mustafatokmak-st/claude-projects/agentic-ai-hack/.env") if l.startswith("OPENROUTER_API_KEY=")][0]


def ask_jev(state, qs):
    req = urllib.request.Request("https://openrouter.ai/api/alpha/decisions",
        data=json.dumps({"model": "typesafe/jev-1.13", "state": state, "questions": qs}).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    t0 = time.perf_counter()
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return r, (time.perf_counter() - t0) * 1000


def ask_text(field):
    body = {"model": "openai/gpt-5.6-luna",
            "messages": [{"role": "user", "content": f"Goal: {GOAL}\nField to fill: {field}\nReply with JSON only: {{\"text\": \"<short value to type>\"}}"}],
            "response_format": {"type": "json_object"}}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return json.loads(r["choices"][0]["message"]["content"])["text"]


def snapshot():
    nodes = cdp("Accessibility.getFullAXTree")["nodes"]
    els = []
    vals = js("(function(){const m={};document.querySelectorAll('input,select,textarea').forEach((el,i)=>{const k=el.getAttribute('aria-label')||el.name||el.type||('f'+i);m[k]=(el.value||'').slice(0,80)});return m})")
    for n in nodes:
        role = n.get("role", {}).get("value", "?")
        name = (n.get("name", {}).get("value", "") or "").strip()
        if role in ("button", "link", "textbox", "combobox", "radio", "checkbox", "searchbox") and name:
            extra = f" value={vals.get(name,'')!r}" if role in ("textbox", "searchbox", "combobox") else ""
            els.append((role, name + extra, n.get("backendDOMNodeId")))
    return els


def center(bid):
    q = cdp("DOM.getBoxModel", backendNodeId=bid)["model"]["content"]
    xs, ys = q[0::2], q[1::2]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def type_replace(bid, txt):
    cdp("DOM.focus", backendNodeId=bid)
    js("(function(){const el=document.activeElement;if(el&&el.select)el.select();return 1})()")
    cdp("Input.insertText", text=txt)
    return js("(document.activeElement&&document.activeElement.value||'').slice(0,60)")


OPC = {"CLICK": "click a control", "TYPE_TEXT": "type into a field (replaces field content)",
       "SELECT": "pick a dropdown/radio option", "WAIT": "wait for load",
       "DONE": "task complete, stop", "BLOCKED": "cannot proceed"}

start_recording("jev-live-rerun", title="Jev live browser demo rerun")
new_tab("http://127.0.0.1:8767/")
wait_for_load()
js("localStorage.clear()")
new_tab("http://127.0.0.1:8767/")
wait_for_load()

tot_ms = 0
tot_cost = 0.0
history = ["fresh start, empty cart"]
for step in range(1, 21):
    els = snapshot()
    table = "\n".join(f"[{i+1}] {r} {n!r}" for i, (r, n, b) in enumerate(els))
    state = (f"Goal: {GOAL}\nURL: {page_info()['url']}\nElements:\n{table}\n"
             f"Recent: {'; '.join(history[-3:])}\n"
             f"Rules: (1) Typing REPLACES field content; filled fields need no retyping. "
             f"(2) DONE only when the review summary with GBP 42.99 is visible. Never click Pay.")
    qs = {"operation": {"type": "choice", "instructions": "Pick the next browser operation", "criteria": OPC},
          "click_target": {"type": "choice", "instructions": "If CLICK, which element index",
                           "criteria": {str(i + 1): f"{r} {n}" for i, (r, n, b) in enumerate(els)}}}
    boxes = [(i + 1, r, n) for i, (r, n, b) in enumerate(els) if r in ("textbox", "searchbox")]
    if boxes:
        qs["type_target"] = {"type": "choice", "instructions": "If TYPE_TEXT, which element index",
                             "criteria": {str(i): f"{r} {n}" for i, r, n in boxes}}
    resp, ms = ask_jev(state, qs)
    tot_ms += ms
    tot_cost += resp["usage"]["cost"]
    op, tgt = resp["answers"]["operation"], resp["answers"]["click_target"]
    oc, opp = op["choice"], op["probabilities"][op["choice"]]
    tc, tpp = tgt["choice"], tgt["probabilities"][tgt["choice"]]
    detail = ""
    try:
        if oc == "CLICK":
            bid = els[int(tc) - 1][2]
            x, y = center(bid)
            click_at_xy(x, y)
            time.sleep(0.8)
            try:
                wait_for_load()
            except Exception:
                pass
            detail = f"clicked [{tc}]"
        elif oc == "TYPE_TEXT":
            ttc = resp["answers"]["type_target"]["choice"]
            bid = els[int(ttc) - 1][2]
            txt = ask_text(els[int(ttc) - 1][1])
            now = type_replace(bid, txt)
            time.sleep(0.5)
            detail = f"typed {txt!r} into [{ttc}], field now {now!r}"
        elif oc == "SELECT":
            bid = els[int(tc) - 1][2]
            x, y = center(bid)
            click_at_xy(x, y)
            time.sleep(0.6)
            detail = f"selected [{tc}]"
        elif oc == "WAIT":
            time.sleep(1.2)
            detail = "waited"
        else:
            detail = "stop"
            print(f"{step:>2} {oc} {opp:.2f} ms={ms:.0f} {detail}", flush=True)
            break
    except Exception as e:
        detail = f"EXEC FAIL {type(e).__name__}"
    after = page_info()["url"]
    history.append(f"{oc} {detail} -> {after}")
    print(f"{step:>2} {oc:>9} {opp:.2f} tgt[{tc}] {tpp:.2f} ms={ms:.0f} {detail} | {after}", flush=True)
    if oc in ("DONE", "BLOCKED"):
        break
print(f"TOTAL jev {tot_ms/1000:.1f}s cost ${tot_cost:.6f}")
print("VERIFY:", js("document.body.innerText.replace(/\\s+/g,' ').slice(0,300)"))
print(stop_recording())
