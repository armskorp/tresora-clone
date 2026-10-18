/* Shop configuration – safe to commit (no secrets here).
   CHECKOUT_URL: URL of the deployed checkout backend (see checkout-server/README.md), e.g.
     "https://tresora-checkout.<your-subdomain>.workers.dev/checkout"
   Leave empty to show a "payments coming soon" message instead of redirecting to payment. */
window.TRESORA_CONFIG = {
  CHECKOUT_URL: "",
  CURRENCY: "USD",
  MAX_QTY_PER_LINE: 20
};
