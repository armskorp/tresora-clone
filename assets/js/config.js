/* Shop configuration – safe to commit (no secrets here).

   CHECKOUT_URL  URL of the checkout backend (Supabase edge function supabase/functions/checkout), e.g.
                 "https://tresora-checkout.<your-subdomain>.workers.dev/checkout".
                 When set, the cart's Checkout button creates ONE Stripe Checkout Session for the whole cart (recommended).

   PAYMENT_LINKS INTERIM checkout that needs no server: "test" or "live" picks a set of Stripe Payment Links from
                 assets/js/payment-links.js (one link per product variant, made by tools/stripe_sync.py).
                 Each link pays for ONE product (the customer can change the quantity on the Stripe page). Used only when
                 CHECKOUT_URL is empty. Set to "" to turn it off.

   SHOPIFY_CHECKOUT_DOMAIN  Shopify store domain (tresora.store). When set, it WINS over CHECKOUT_URL and PAYMENT_LINKS:
                 the cart's Checkout button sends the WHOLE cart to ONE Shopify checkout through a cart permalink
                 https://tresora.store/cart/VARIANT_ID:QTY,VARIANT_ID:QTY (catalog variant ids are the Shopify variant ids).
                 Greeting card / message / lid inscription go into the Shopify order note. Payment, tax and the order
                 itself are handled by Shopify (same payouts as tresora.store). Set to "" to go back to the Stripe checkout below
                 (CHECKOUT_URL / PAYMENT_LINKS are kept as the fallback and are not used while this is set).

   If none is set, Checkout shows a friendly "payments coming soon" message.

   WELCOME_POPUP  true = show the "15% off" email popup (assets/js/welcome.js) to new visitors; false = hidden
                  (still testable with ?welcome=1). WELCOME_CODE is the Stripe promotion code the popup shows. */
window.TRESORA_CONFIG = {
  SHOPIFY_CHECKOUT_DOMAIN: "tresora.store",
  CHECKOUT_URL: "https://bnequlkhwcnuzplsdktp.supabase.co/functions/v1/checkout",
  PAYMENT_LINKS: "live",
  CURRENCY: "USD",
  MAX_QTY_PER_LINE: 20,
  WELCOME_POPUP: true,
  WELCOME_CODE: "WELCOME15"
};
