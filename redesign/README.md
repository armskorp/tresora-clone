# TRESORA redesign concepts (preview only)

Three complete, browsable mini-sites built from the real catalog (12 products, real prices, real photos, the 5 real reviews at 5.00).
The live homepage at the repo root is not changed.

| Concept | URL | Look |
|---|---|---|
| v1 Midnight | /redesign/v1/ | Deep navy + emerald with ivory and soft silver. Centered editorial header, hero mosaic of real items (Vermeer mini print, Barcelona mosaic fan, Paris pearl bag) |
| v2 Gallery | /redesign/v2/ | Cream, burgundy + terracotta, museum-label typography, framed hero: the mini Vermeer print |
| v3 Modern | /redesign/v3/ | White + cobalt, clean sans, split hero with the Amalfi pieces, dense 4-column shop |

Product-first: every hero, tile and card shows the items themselves, not the packaging (`tools/prep_redesign_images.py` builds the lead images / crops from the store's own gallery). Product pages lead with item photos and a numbered “What’s inside” list parsed from the real descriptions; packaging is a one-line note.

Each concept has: `index.html` (home), `shop.html` (category filter, in-stock filter, sort, search via `?q=`/`?cat=`),
`products/<handle>.html` for all 12 products (gallery, variants, quantity, description, related), `cart.html`
(full cart with quantity / remove / Stripe checkout) and `account.html` (sign in / create account, `?mode=signup`).

- Cart, drawer and checkout are the site's real `assets/js/cart.js` (shared localStorage cart, Stripe Payment Links in test mode).
- Account and newsletter forms are front-end previews only: nothing is sent or stored.
- Build: `python3 tools/build_redesign.py`. Check: `python3 tools/redesign_check.py https://armskorp.github.io/tresora-clone/`.

## What real customer accounts need
An auth backend (e.g. Shopify customer accounts, or Supabase/Auth0/Clerk) with hashed passwords, email verification and
password-reset emails sent through a transactional provider (Postmark, SendGrid, Amazon SES or Resend) on a verified domain
(SPF, DKIM, DMARC for tresora.store). Order history needs Stripe Checkout webhooks stored per customer.
The newsletter needs a list provider (Klaviyo, Mailchimp, Shopify Email) with double opt-in and unsubscribe links.
