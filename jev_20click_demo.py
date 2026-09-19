import json, os, re, sys, time, urllib.request

ENV = os.path.join(os.path.dirname(__file__), ".env")
KEY = re.search(r'OPENROUTER_API_KEY=(\S+)', open(ENV).read()).group(1)
JEV = "typesafe/jev-1.13"
GOAL = "Buy an Aurora 65W USB-C charger on the demo shop as guest and reach the order-review step."

# (url, elements [(idx, desc)], recent, note)
STEPS = [
 ("https://demo-shop.test/", [("1","search box 'Search products'"),("2","button 'Sign in'"),("3","link 'Deals'")], "page just loaded", "type query"),
 ("https://demo-shop.test/", [("1","search box value='usb-c charger'"),("2","button 'Search'"),("3","link 'Deals'")], "typed 'usb-c charger'", "submit search"),
 ("https://demo-shop.test/search?q=usb-c+charger", [("1","link 'Aurora 65W USB-C Charger'"),("2","link 'VoltPro 100W Dock'"),("3","button 'Next page'")], "results loaded, 12 items", "open product"),
 ("https://demo-shop.test/p/aurora-65w", [("1","button 'Add to cart'"),("2","button 'Quantity +1'"),("3","link 'Reviews (214)'")], "product page, price £39", "add to cart"),
 ("https://demo-shop.test/p/aurora-65w", [("1","text 'Added to cart ✓'"),("2","button 'Go to cart'"),("3","button 'Keep shopping'")], "cart drawer opened", "wait settles"),
 ("https://demo-shop.test/p/aurora-65w", [("1","button 'Go to cart'"),("2","button 'Keep shopping'"),("3","link 'Aurora 65W USB-C Charger'")], "drawer ready", "go to cart"),
 ("https://demo-shop.test/cart", [("1","button 'Proceed to checkout'"),("2","button 'Quantity +1'"),("3","button 'Remove'")], "cart shows 1 × £39", "checkout"),
 ("https://demo-shop.test/checkout#email", [("1","textbox 'Email'"),("2","button 'Continue'"),("3","link 'Back to cart'")], "checkout step 1, email empty", "type email"),
 ("https://demo-shop.test/checkout#address", [("1","textbox 'Street address'"),("2","textbox 'Postcode'"),("3","button 'Continue'")], "email filled", "type address"),
 ("https://demo-shop.test/checkout#address", [("1","dropdown 'Country' value=United Kingdom"),("2","button 'Continue'"),("3","link 'Back'")], "address typed", "confirm country"),
 ("https://demo-shop.test/checkout#address", [("1","button 'Continue to shipping'"),("2","link 'Back'"),("3","text '1 × Aurora 65W — £39'")], "form complete", "continue"),
 ("https://demo-shop.test/checkout#shipping", [("1","text 'Loading shipping options…'"),("2","button 'Continue to payment' (disabled)"),("3","link 'Back'")], "navigated, options loading", "wait load"),
 ("https://demo-shop.test/checkout#shipping", [("1","radio 'Standard 3-5 days — £3.99'"),("2","radio 'Express — £7.99'"),("3","button 'Continue to payment'")], "2 options rendered", "pick standard"),
 ("https://demo-shop.test/checkout#shipping", [("1","button 'Continue to payment'"),("2","radio 'Standard 3-5 days — £3.99' (selected)"),("3","link 'Back'")], "standard selected", "continue"),
 ("https://demo-shop.test/checkout#payment", [("1","textbox 'Card number'"),("2","textbox 'Expiry'"),("3","button 'Review order'")], "payment step, empty", "type card"),
 ("https://demo-shop.test/checkout#payment", [("1","textbox 'Expiry' value=empty"),("2","textbox 'CVC' value=empty"),("3","button 'Review order'")], "card number filled", "type expiry/cvc"),
 ("https://demo-shop.test/checkout#payment", [("1","dropdown 'Billing country' value=United Kingdom"),("2","button 'Review order'"),("3","link 'Back'")], "card details filled", "confirm billing"),
 ("https://demo-shop.test/checkout#payment", [("1","button 'Review order'"),("2","link 'Back'"),("3","text 'Total £42.99'")], "form complete", "review"),
 ("https://demo-shop.test/checkout#review", [("1","text 'Order summary'"),("2","button 'Pay £42.99'"),("3","link 'Edit payment'")], "review rendering", "wait render"),
 ("https://demo-shop.test/checkout#review", [("1","text 'Aurora 65W × 1 — Total £42.99'"),("2","button 'Pay £42.99'"),("3","text 'Shipping to guest@demo.test'")], "matching options visible, DO NOT pay", "finish"),
]

OP_CRITERIA = {"CLICK":"click a control","TYPE_TEXT":"type into a field","SELECT":"pick a dropdown/radio option",
               "WAIT":"wait for page load","DONE":"task complete, stop","BLOCKED":"cannot proceed"}

def post(body):
    return urllib.request.Request("https://openrouter.ai/api/alpha/decisions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})

print(f"20-click browser demo | goal: {GOAL}\n")
print(f"{'step':>4} {'op':>9} {'p':>5} {'target':>7} {'p':>5} {'ms':>6}  action")
total_ms = total_cost = 0.0
from collections import Counter
ops = Counter()
fails = 0
for i, (url, els, recent, note) in enumerate(STEPS, 1):
    el_lines = "\n".join(f"[{idx}] {d}" for idx, d in els)
    state = (f"Goal: {GOAL}\nStep {i}/20 ({note}).\nURL: {url}\nElements:\n{el_lines}\nRecent: {recent}.\n"
             f"Rule: DONE only at step 20 when the review summary is visible. Never choose Pay.")
    qs = {"operation": {"type": "choice", "instructions": "Pick the next browser operation",
                        "criteria": OP_CRITERIA},
          "click_target": {"type": "choice", "instructions": "If CLICK, which element index",
                           "criteria": {idx: d for idx, d in els}}}
    t0 = time.perf_counter()
    try:
        resp = json.loads(urllib.request.urlopen(post(
            {"model": JEV, "state": state, "questions": qs}), timeout=60).read())
        ms = (time.perf_counter() - t0) * 1000
        op = resp["answers"]["operation"]; tgt = resp["answers"]["click_target"]
        op_c, op_p = op["choice"], op["probabilities"][op["choice"]]
        t_c, t_p = tgt["choice"], tgt["probabilities"][tgt["choice"]]
        total_ms += ms; total_cost += resp["usage"]["cost"]; ops[op_c] += 1
        tdesc = dict(els).get(t_c, "?")
        print(f"{i:>4} {op_c:>9} {op_p:>5.2f} [{t_c:>3}] {t_p:>5.2f} {ms:>6.0f}  {op_c} {t_c} ({tdesc[:42]})")
    except Exception as e:
        fails += 1
        print(f"{i:>4} FAILED {type(e).__name__}: {str(e)[:100]}")

print(f"\n20 steps: {20-fails} ok, {fails} failed | total {total_ms/1000:.1f}s, avg {total_ms/max(1,20-fails):.0f}ms/decision, cost ${total_cost:.6f}")
print("ops mix:", dict(ops))
print("Note: synthetic states (no live Chrome); each row is one real Jev fan-out call: operation + target heads, one round trip.")
