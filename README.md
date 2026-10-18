# TRESORA homepage – static copy

An offline, static copy of the homepage of [tresora.store](https://tresora.store/) (TRESORA Gifts – art & city inspired gift boxes).
It is plain HTML/CSS with a small amount of JavaScript (`assets/js/clone.js`). It has no Shopify runtime and makes no network requests.

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

## What doesn't work

These things need the Shopify backend, so they are inert in the copy:

- cart
- search
- account
- quick add
- newsletter and gift-finder forms
- links other than the product pages (they point to `#`)
