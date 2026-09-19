#!/usr/bin/env python3
"""Local demo shop for the live Jev browser demo. Run: python3 realshop_server.py [--port 8767]."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

STYLE = "<style>body{font-family:system-ui;max-width:640px;margin:40px auto;padding:0 20px}button,input,select{font-size:16px;padding:8px 12px;margin:6px 0}a{font-size:17px}.card{border:1px solid #ccc;padding:14px;margin:12px 0}.price{font-weight:700}</style>"

HOME = f"""<!doctype html><html><head><meta charset=utf-8><title>Demo Shop</title>{STYLE}</head><body>
<h1>Demo Shop</h1>
<form action="/search" method="get">
<input name="q" aria-label="Search products" placeholder="Search products" value="">
<button type="submit">Search</button>
</form>
<p><a href="/deals">Today's deals</a> | <a href="/cart">Cart (<span id=c>0</span>)</a></p>
<script>document.getElementById('c').textContent=JSON.parse(localStorage.getItem('cart')||'[]').length</script>
</body></html>"""

RESULTS = f"""<!doctype html><html><head><meta charset=utf-8><title>Results</title>{STYLE}</head><body>
<h1>Results for "charger"</h1>
<div class=card><a href="/p/aurora">Aurora 65W USB-C Charger</a> <span class=price>£39.00</span> ★★★★★ (214)</div>
<div class=card><a href="/p/voltpro">VoltPro 100W Dock</a> <span class=price>£89.00</span> ★★★★ (98)</div>
<div class=card><a href="/p/nimbo">Nimbo 30W Mini</a> <span class=price>£19.00</span> ★★★★ (41)</div>
<p><a href="/">Back home</a></p></body></html>"""

PRODUCT = f"""<!doctype html><html><head><meta charset=utf-8><title>Aurora 65W</title>{STYLE}</head><body>
<h1>Aurora 65W USB-C Charger</h1><p class=price>£39.00</p>
<button id=add aria-label="Add Aurora 65W to cart">Add to cart</button>
<p id=msg role=status></p>
<p><a href="/cart" id=gocart>Go to cart</a> | <a href="/search?q=charger">Back to results</a></p>
<script>document.getElementById('add').onclick=()=>{{const c=JSON.parse(localStorage.getItem('cart')||'[]');c.push('aurora');localStorage.setItem('cart',JSON.stringify(c));document.getElementById('msg').textContent='Added to cart ✓';}};</script>
</body></html>"""

CART = f"""<!doctype html><html><head><meta charset=utf-8><title>Cart</title>{STYLE}</head><body>
<h1>Your cart</h1><div id=items class=card></div>
<p><a href="/checkout" id=checkout>Proceed to checkout</a> | <a href="/">Keep shopping</a></p>
<script>const c=JSON.parse(localStorage.getItem('cart')||'[]');
document.getElementById('items').textContent=c.length?c.length+' × Aurora 65W USB-C Charger — £'+(39*c.length).toFixed(2):'Cart is empty';</script>
</body></html>"""

CHECKOUT = f"""<!doctype html><html><head><meta charset=utf-8><title>Checkout</title>{STYLE}</head><body>
<h1>Checkout — contact</h1>
<label>Email <input id=email aria-label="Email" inputmode=email placeholder="you@example.com"></label><br>
<label>Street address <input id=addr aria-label="Street address" placeholder="221B Baker Street"></label><br>
<label>Country <select id=country aria-label="Country"><option>United Kingdom</option><option>Germany</option><option>United States</option></select></label><br>
<p><a href="/shipping" id=cont>Continue to shipping</a></p>
<script>for(const id of ['email','addr']){{document.getElementById(id).value=localStorage.getItem(id)||'';document.getElementById(id).oninput=e=>localStorage.setItem(id,e.target.value);}}</script>
</body></html>"""

SHIPPING = f"""<!doctype html><html><head><meta charset=utf-8><title>Shipping</title>{STYLE}</head><body>
<h1>Checkout — shipping</h1>
<label><input type=radio name=ship value=standard checked> Standard 3-5 days — £3.99</label><br>
<label><input type=radio name=ship value=express> Express next day — £7.99</label><br>
<p><a href="/review" id=topay>Continue to review</a> | <a href="/checkout">Back</a></p>
</body></html>"""

REVIEW = f"""<!doctype html><html><head><meta charset=utf-8><title>Review</title>{STYLE}</head><body>
<h1>Order review</h1>
<div class=card id=sum>1 × Aurora 65W USB-C Charger — £39.00 + £3.99 shipping = <b>£42.99</b><br>Guest checkout as <span id=who>(no email yet)</span></div>
<button id=pay disabled>Pay £42.99 (disabled in demo)</button>
<p><a href="/shipping">Back</a></p>
<script>document.getElementById('who').textContent=localStorage.getItem('email')||'(no email yet)';</script>
</body></html>"""

PAGES = {"/": HOME, "/search": RESULTS, "/p/aurora": PRODUCT, "/p/voltpro": PRODUCT,
         "/p/nimbo": PRODUCT, "/cart": CART, "/checkout": CHECKOUT, "/shipping": SHIPPING,
         "/review": REVIEW, "/deals": RESULTS}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        body = PAGES.get(path)
        if body is None:
            self.send_response(404); self.end_headers(); return
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=8767)
    args = ap.parse_args()
    HTTPServer(("127.0.0.1", args.port), H).serve_forever()
