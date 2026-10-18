"""Print the status of a Stripe Checkout Session (non-secret fields only).  usage: python3 tools/stripe_verify.py cs_test_..."""
import json, os, sys, urllib.request
KEY = os.environ["STRIPE_SECRET_KEY"]
def get(path):
    r = urllib.request.Request("https://api.stripe.com/v1/" + path); r.add_header("Authorization", "Bearer " + KEY)
    return json.load(urllib.request.urlopen(r, timeout=30))
s = get(f"checkout/sessions/{sys.argv[1]}?expand[]=line_items&expand[]=payment_intent")
pi = s.get("payment_intent") or {}
print(json.dumps({"session": s["id"], "livemode": s["livemode"], "status": s["status"], "payment_status": s["payment_status"],
  "amount_total": s["amount_total"], "currency": s["currency"], "payment_link": s.get("payment_link"),
  "line_items": [{"desc": li["description"], "qty": li["quantity"], "unit": li["price"]["unit_amount"], "total": li["amount_total"]} for li in s["line_items"]["data"]],
  "payment_intent": pi.get("id"), "pi_status": pi.get("status"), "metadata": s.get("metadata"), "pi_metadata": pi.get("metadata"),
  "shipping_country": ((s.get("shipping_details") or s.get("collected_information", {}).get("shipping_details") or {}).get("address") or {}).get("country")}, indent=1))
