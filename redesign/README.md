# TRESORA homepage design concepts (preview)

The live homepage (`/index.html`) is unchanged. These pages only add new URLs.

| Concept | URL | Idea |
|---|---|---|
| v1 Luxury dark | `/redesign/v1/` | Midnight navy and emerald with ivory and soft-silver accents, large serif headlines, boutique feel (no gold). |
| v2 Warm gallery | `/redesign/v2/` | Burgundy and terracotta on cream. Museum frame hero, "rooms" for categories, framed product cards, guest-book reviews. |
| v3 Modern clean shop | `/redesign/v3/` | White with cobalt as the only brand color. Banner and promo hero, dense 4-column grid, marketplace clarity. |

All three use the real catalog: 12 products, real prices and real photos from `assets/js/catalog.js`. They show the 5 real reviews (5.00) and use the site's working cart (`assets/js/cart.js`, the same drawer and Stripe test checkout). Build: `python3 tools/build_redesign.py`. Check: `python3 tools/redesign_check.py BASE_URL [--shots]`.

**Front-end only, for now:**
- Sign in / Create account: validates email and password, then shows a "preview" message. Nothing is sent or stored.
- Newsletter: validates email and consent, then shows a "preview" message. Nothing is sent.

Real accounts and email sign-up need a backend: an auth service or database, password hashing, email verification and reset emails, and an email provider or mailing list.
