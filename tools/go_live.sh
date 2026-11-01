#!/usr/bin/env bash
# Switch tresoragift.com checkout from Stripe TEST to LIVE Payment Links.
# Needs STRIPE_SECRET_KEY=sk_live_... (or rk_live_ with products/prices/payment_links write) in the environment. Never printed or committed.
set -euo pipefail
cd /workspace/tresora-clone
k="${STRIPE_SECRET_KEY:-}"; [[ "$k" == sk_live_* || "$k" == rk_live_* ]] || { echo "BLOCKED: STRIPE_SECRET_KEY is not a live key (${k:0:8})"; exit 2; }
curl -sf -u "$k:" https://api.stripe.com/v1/account | python3 -c 'import json,sys;a=json.load(sys.stdin);print("account",a["id"],"charges_enabled",a.get("charges_enabled"),"payouts_enabled",a.get("payouts_enabled"));sys.exit(0 if a.get("charges_enabled") else 3)'
export SITE=https://tresoragift.com
python3 tools/stripe_sync.py          # -> stripe/ids-live.json (public ids/urls only)
python3 tools/build_shop.py           # -> assets/js/payment-links.js gets a "live" set
python3 - <<'PY'
import json,re
s=open("assets/js/payment-links.js").read(); d=json.loads(re.search(r"=\s*(\{.*\});",s,re.S).group(1))
assert d.get("live") and all(u.startswith("https://buy.stripe.com/") and "/test_" not in u for u in d["live"].values()), "live links missing"
p="assets/js/config.js"; c=open(p).read(); c=re.sub(r'PAYMENT_LINKS:\s*"[a-z]*"','PAYMENT_LINKS: "live"',c); open(p,"w").write(c)
print("live links:",len(d["live"]),"; config PAYMENT_LINKS=live")
PY
python3 tools/build_redesign.py | tail -1
git add assets/js stripe/ids-live.json checkout-server/src/catalog.js tools && git -c user.name=armskorp -c user.email=armskorp@users.noreply.github.com commit -qm "Checkout: switch to LIVE Stripe Payment Links on tresoragift.com" && git push -q origin main && git log --oneline -1
