"""Create or update the TRESORA catalog in Stripe: one Product per store product, one Price per variant,
and one Payment Link per available variant (the interim, no-server checkout).

  STRIPE_SECRET_KEY must be set in the environment (it is never printed or written to disk).
  python3 tools/stripe_sync.py            -> writes stripe/ids-<test|live>.json (public IDs/URLs only, no secrets)

The script is idempotent: it finds existing objects by metadata (shopify_product_id / shopify_variant_id + amount)
and reuses the Payment Links recorded in the ids file."""
import json, os, re, sys, time, html, urllib.request, urllib.parse, urllib.error
ROOT = "/workspace/tresora-clone"; os.chdir(ROOT)
SITE = "https://armskorp.github.io/tresora-clone"
KEY = os.environ.get("STRIPE_SECRET_KEY", "")
if not KEY.startswith(("sk_test_", "sk_live_", "rk_test_", "rk_live_")): sys.exit("STRIPE_SECRET_KEY missing or malformed")
MODE = "live" if "_live_" in KEY[:8] else "test"
OUT = f"stripe/ids-{MODE}.json"
catalog = json.load(open("orig/products.json"))["products"]
client = json.loads(re.search(r"=\s*(\{.*\});", open("assets/js/catalog.js").read(), re.S).group(1))
prev = json.load(open(OUT)) if os.path.exists(OUT) else {"products": {}, "variants": {}}

def flat(d, prefix=""):
    out = []
    for k, v in d.items():
        key = f"{prefix}[{k}]" if prefix else k
        if isinstance(v, dict): out += flat(v, key)
        elif isinstance(v, list):
            for i, x in enumerate(v):
                out += flat(x, f"{key}[{i}]") if isinstance(x, dict) else [(f"{key}[{i}]", x)]
        elif isinstance(v, bool): out.append((key, "true" if v else "false"))
        else: out.append((key, v))
    return out

def api(method, path, params=None, idem=None):
    data = urllib.parse.urlencode(flat(params or {})).encode() if method == "POST" else None
    url = "https://api.stripe.com/v1/" + path + ("?" + urllib.parse.urlencode(flat(params)) if method == "GET" and params else "")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + KEY); req.add_header("Stripe-Version", "2024-06-20")
    if idem: req.add_header("Idempotency-Key", idem)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            body = json.load(e)
            if e.code in (429, 500, 502, 503) and attempt < 3: time.sleep(1 + 2 * attempt); continue
            sys.exit(f"Stripe API error {e.code} on {method} {path}: {body.get('error', {}).get('message')}")

def search(kind, query):
    return api("GET", f"{kind}/search", {"query": query, "limit": 10})["data"]

def plain(htm, n=300):
    t = re.sub(r"<[^>]+>", " ", htm or ""); t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    return (t[: n - 1] + "…") if len(t) > n else t

ids = {"mode": MODE, "products": {}, "variants": {}}
for p in catalog:
    pid = str(p["id"]); cp = client["products"][pid]
    found = [x for x in search("products", f"metadata['shopify_product_id']:'{pid}'") if x.get("active")]
    params = {"name": p["title"], "description": plain(p.get("body_html")) or p["title"],
              "images": [f"{SITE}/{cp['image']}"], "url": f"{SITE}/products/{p['handle']}.html",
              "metadata": {"shopify_product_id": pid, "handle": p["handle"]}}
    prod = api("POST", f"products/{found[0]['id']}", params) if found else api("POST", "products", params, idem=f"tresora-product-{pid}")
    ids["products"][pid] = {"stripe_product": prod["id"], "title": p["title"]}
    for v in p["variants"]:
        vid = str(v["id"]); cv = client["variants"][vid]; amount = cv["price"]
        prices = [x for x in search("prices", f"metadata['shopify_variant_id']:'{vid}' AND active:'true'")
                  if x["unit_amount"] == amount and x["currency"] == "usd" and x["product"] == prod["id"]]
        price = prices[0] if prices else api("POST", "prices", {
            "product": prod["id"], "currency": "usd", "unit_amount": amount, "nickname": cv["variant_title"] or p["title"],
            "metadata": {"shopify_variant_id": vid, "shopify_product_id": pid, "variant_title": cv["variant_title"]}},
            idem=f"tresora-price-{vid}-{amount}")
        rec = {"stripe_price": price["id"], "amount": amount, "available": cv["available"], "name": p["title"] + (f" – {cv['variant_title']}" if cv["variant_title"] else "")}
        old = prev["variants"].get(vid, {})
        if cv["available"]:
            if old.get("stripe_price") == price["id"] and old.get("payment_link"):
                rec.update({k: old[k] for k in ("payment_link", "payment_link_url")})
            else:
                link = api("POST", "payment_links", {
                    "line_items": [{"price": price["id"], "quantity": 1, "adjustable_quantity": {"enabled": True, "minimum": 1, "maximum": 20}}],
                    "after_completion": {"type": "redirect", "redirect": {"url": f"{SITE}/success.html?session_id={{CHECKOUT_SESSION_ID}}"}},
                    "shipping_address_collection": {"allowed_countries": ["US"]},
                    "billing_address_collection": "auto",
                    "metadata": {"shopify_variant_id": vid, "shopify_product_id": pid, "source": "tresora-static-site"},
                    "payment_intent_data": {"metadata": {"shopify_variant_id": vid, "item": rec["name"][:200]}},
                    **({"custom_text": {"submit": {"message": f"{p['options'][0]['name']}: {cv['variant_title']}"}}} if cv["variant_title"] else {}),
                }, idem=f"tresora-plink-{vid}-{price['id']}")
                rec.update({"payment_link": link["id"], "payment_link_url": link["url"]})
        elif old.get("payment_link"):  # sold out: deactivate an existing link
            api("POST", f"payment_links/{old['payment_link']}", {"active": False})
        ids["variants"][vid] = rec
        print(f"{MODE}: {rec['name']:<52} ${amount/100:>6.2f}  {price['id']}  {rec.get('payment_link_url', '(sold out, no link)')}")

json.dump(ids, open(OUT, "w"), indent=1)
print(f"wrote {OUT}: {len(ids['products'])} products, {len(ids['variants'])} prices, {sum(1 for v in ids['variants'].values() if v.get('payment_link'))} payment links")
