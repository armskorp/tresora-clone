/* Shop configuration – safe to commit (no secrets here).

   CHECKOUT_URL  URL of the deployed checkout backend (checkout-server/, a Cloudflare Worker), e.g.
                 "https://tresora-checkout.<your-subdomain>.workers.dev/checkout".
                 When set, the cart's Checkout button creates ONE Stripe Checkout Session for the whole cart (recommended).

   PAYMENT_LINKS INTERIM checkout that needs no server: "test" or "live" picks a set of Stripe Payment Links from
                 assets/js/payment-links.js (one link per product variant, made by tools/stripe_sync.py).
                 Each link pays for ONE product (the customer can change the quantity on the Stripe page). Used only when
                 CHECKOUT_URL is empty. Set to "" to turn it off.

   If neither is set, Checkout shows a friendly "payments coming soon" message. */
window.TRESORA_CONFIG = {
  CHECKOUT_URL: "",
  PAYMENT_LINKS: "test",
  CURRENCY: "USD",
  MAX_QTY_PER_LINE: 20
};
