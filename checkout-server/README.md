# TRESORA checkout server (Cloudflare Worker + Stripe Checkout)

This is a small serverless endpoint. It turns the static site's cart into a **Stripe Checkout Session** and returns that session's URL. The site's Checkout button then sends the shopper to the URL.

```
browser cart ──POST /checkout {items:[{variant_id, product_id, quantity}]}──▶ Worker ──▶ Stripe API
            ◀────────────── {url: "https://checkout.stripe.com/…"} ─────────────┘
shopper pays on Stripe ──▶ redirected to SITE_URL/success.html?session_id=…  (or cancel.html)
```

## How prices stay safe
- Prices, names and availability come only from `src/catalog.js`. `tools/build_shop.py` generates that file from the store's `products.json`, and Wrangler bundles it at deploy time. **Any price the client sends is ignored.**
- Unknown or sold-out variants are rejected. A `product_id` that doesn't match its variant is rejected. Quantities must be integers from 1 to 20, with at most 25 lines.
- Where `tools/stripe_sync.py` created Stripe Prices, the Worker uses those Price IDs. It picks test or live IDs to match the key. Variants with an option (such as a blanket color) are sent inline with the server amount, so the color shows on Stripe's page.
- CORS only allows `ALLOWED_ORIGINS`. Stripe errors are logged but never returned to the browser.
- `STRIPE_SECRET_KEY` is a **Worker secret**. It is never in the repo, `wrangler.toml` or logs.

## Configuration
| Name | Kind | Example |
| --- | --- | --- |
| `STRIPE_SECRET_KEY` | **secret** (`wrangler secret put`) | `sk_test_…` while testing, `sk_live_…` for real payments |
| `SITE_URL` | var (`wrangler.toml`) | `https://armskorp.github.io/tresora-clone` |
| `ALLOWED_ORIGINS` | var | `https://armskorp.github.io` (comma-separated) |
| `STRIPE_AUTOMATIC_TAX` | var | `"true"` once Stripe Tax is set up |
| `USE_STRIPE_PRICE_IDS` | var (optional) | `"false"` to always send inline amounts |

## Deploy (Cloudflare Workers, free plan)
1. Create a free Cloudflare account at https://dash.cloudflare.com/sign-up. No domain or card is needed for `*.workers.dev`.
2. From this folder, run:
   ```bash
   npm install
   npx wrangler login                       # opens the browser once
   npx wrangler secret put STRIPE_SECRET_KEY   # paste sk_test_… (later sk_live_…)
   npx wrangler deploy                      # prints https://tresora-checkout.<subdomain>.workers.dev
   ```
3. In the site, set `CHECKOUT_URL` in `assets/js/config.js` to `https://tresora-checkout.<subdomain>.workers.dev/checkout`. Then commit and push; GitHub Pages redeploys.
4. Test with card `4242 4242 4242 4242`, any future date and any CVC.

For CI deploys instead, create a Cloudflare API token ("Edit Cloudflare Workers" template). Store it as the GitHub Actions secret `CLOUDFLARE_API_TOKEN`, then run `npx wrangler deploy`.

## Going live
1. Activate the Stripe account (business details and bank account). Then switch to live keys.
2. Run `STRIPE_SECRET_KEY=sk_live_… python3 tools/stripe_sync.py`. This creates live products, prices and links in `stripe/ids-live.json`. Then run `python3 tools/build_shop.py`, commit and redeploy the Worker.
3. Run `npx wrangler secret put STRIPE_SECRET_KEY` with the **live** key.
4. Recommended: add a Stripe webhook (`checkout.session.completed`) or turn on email receipts and notifications in the Stripe dashboard, so every order reaches fulfillment. Order contents are in the session and PaymentIntent metadata `cart` (`variantId x qty`), and in the line items.

## Local development and tests
```bash
npm test                                   # unit tests, Stripe mocked
node scripts/local-server.mjs              # Worker on :8787 with Stripe mocked
REAL_STRIPE=1 node scripts/local-server.mjs # Worker on :8787 against the real Stripe TEST API (sk_test_ key from env)
# then:  python3 ../tools/test_stripe_pay.py session http://127.0.0.1:8765/ http://127.0.0.1:8787/checkout
```
`npx wrangler dev` also works. Copy `.dev.vars.example` to `.dev.vars` first; that file is gitignored.

## Other hosts
`src/index.js` is a standard `fetch(request, env)` handler. It ports with little change to Netlify Functions or Vercel (`export default { fetch }` on the edge runtime), or to Deno Deploy. Cloudflare is recommended for the reasons in the top-level README.
