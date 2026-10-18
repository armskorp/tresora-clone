# TRESORA homepage – static copy

An offline, static copy of the homepage of [tresora.store](https://tresora.store/) (TRESORA Gifts – art & city inspired gift boxes).
It is plain HTML/CSS with a small amount of JavaScript (`assets/js/clone.js`, plus the cart in `assets/js/cart.js`). It has no Shopify runtime. The pages load nothing from other sites; only checkout goes to Stripe.

## Run locally

```bash
python3 -m http.server 8765
# open http://localhost:8765/
```

## Layout

| Path | Contents |
| --- | --- |
| `index.html` | The homepage, built from the live page's JS-rendered DOM with scripts, apps and tracking removed |
| `assets/css/` | The theme stylesheets (Shopify Horizon theme, compiled section styles) and Judge.me widget CSS, downloaded from the live site; `clone.css` holds the few local overrides |
| `assets/fonts/` | Cormorant, Josefin Slab and Inter webfonts used by the theme |
| `assets/images/` | Logo, hero, collection, product and review images |
| `assets/js/clone.js` | The minimal JS: mobile menu drawer, desktop submenu hover, product-card gallery arrows, and the review carousel (position, arrows, swipe) |
| `products/*.html` | Simple local placeholder pages for each product, using the title, price, image and description from `/products.json` |
| `screenshots/` | `original-*` (live site) and `copy-*` (this copy), desktop at 1280 px and mobile at 390 px, full page |
| `tools/` | Build, screenshot and comparison scripts |
| `orig/` | Source snapshots used by the build (rendered DOM, raw server HTML, products.json) |

## Rebuild

```bash
python3 tools/build.py                                     # index.html + assets from orig/
python3 tools/capture.py http://127.0.0.1:8765/ screenshots/copy
python3 tools/capture.py https://tresora.store/ screenshots/original
python3 tools/compare.py                                   # pixel diff report
```

## Shop: cart and payments

- **Cart** (`assets/js/cart.js`, `assets/css/shop.css`): Add buttons on the homepage cards, and Add to cart with variant and quantity on every product page. The header cart icon shows the item count. The cart drawer has quantity +/−, Remove and a USD subtotal. The cart is saved in `localStorage` (`tresora_cart_v1`), so it carries across pages and reloads. Display data comes from `assets/js/catalog.js`, which `tools/build_shop.py` generates.
- **Checkout** depends on `assets/js/config.js`:
  1. `CHECKOUT_URL` set: one Stripe Checkout Session for the whole cart, via `checkout-server/` (Cloudflare Worker, see its README). **Recommended.**
  2. Else `PAYMENT_LINKS: "test"` (current setting): the **interim** checkout with no server. Each variant has its own Stripe Payment Link (`assets/js/payment-links.js`). A cart with one product goes straight to that product's link. Otherwise the drawer lists one "Pay for …" link per item. Product pages also show a **Buy now** button. These links are **Stripe test mode**: no real charges; use card 4242 4242 4242 4242.
  3. Neither: a "payments coming soon" message.
- `tools/stripe_sync.py` creates or updates the Stripe Products, Prices and Payment Links (idempotent). It reads `STRIPE_SECRET_KEY` from the environment and writes only public IDs to `stripe/ids-<mode>.json`.
- Tests: `python3 tools/test_cart.py [site]` (cart e2e), `python3 tools/test_stripe_pay.py link|session …` (real test-mode payment), `cd checkout-server && npm test`.

## What doesn't work

These things need a store backend, so they are inert in the copy:

- search
- account
- newsletter and gift-finder forms
- links other than the product pages (they point to `#`)
- inventory: product availability is a snapshot from `products.json`

## Mobile / iOS hardening

`tools/finalize.py` runs at the end of `tools/build_shop.py`:
- Each product card's photo is the first slide. It is a plain eager `<img>` with its real pixel size, and the first two cards of each row load at high priority.
- Local CSS and JS get `?v=<content hash>` so phones never keep stale files.

`assets/css/clone.css` turns off the theme's scroll-driven slider animations and `content-visibility` on slides. On phones and touch screens it shows only the first photo of each card.

Checks: `tools/card_check.py` (iPhone emulation in WebKit or Chromium), `tools/audit_images.py`, `tools/mobile_audit.py`, `tools/phone_shot.py`.
