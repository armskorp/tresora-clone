"""Build 3 homepage design concepts in redesign/v1..v3 from the real catalog (assets/js/catalog.js).
Nothing on the live homepage is touched. usage: python3 tools/build_redesign.py"""
import json, html, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
s = open("assets/js/catalog.js").read()
CAT = json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])
B = "../../"                      # pages live in redesign/vN/
E = html.escape
IMG = B + "assets/images/"
CATS = {
  "art":  {"name": "Inspired by Art", "short": "Art", "img": IMG + "image-10_48088147-e49f-4aaa-bd8a-48d50da18052-w800-af46c8.jpg",
           "blurb": "Klimt, Vermeer, Van Gogh, Caravaggio and Sargent, translated into objects.",
           "handles": ["caravaggio-bacchus-wine-gift-box", "vermeer-girl-with-a-pearl-earring-gift-box", "klimt-the-kiss-gift-box",
                       "van-gogh-almond-blossom-gift-box", "sargent-the-wineglasses-wine-gift-box", "elegant-pearl-earring-table-gift-box"]},
  "city": {"name": "Inspired by City", "short": "City", "img": IMG + "Screenshot_2026-09-12_at_3.44.55_pm-w800-ed034c.png",
           "blurb": "Every city has a feeling. We turn it into a gift.",
           "handles": ["paris-gift-box", "barcelona-gift-box", "new-york-gift-box", "amalfi-gift-box"]},
  "home": {"name": "Atelier Home", "short": "Atelier Home", "img": IMG + "image-5_2ce1ab6c-0c85-4abf-bd9f-62e1497b0377-w800-7e25c9.jpg",
           "blurb": "Handmade objects for a beautiful home.",
           "handles": ["gothic-romance-decorative-glass-bottle", "rococo-reverie-decorative-glass-bottle"]},
}
BY_HANDLE = {p["handle"]: p for p in CAT["products"].values()}
assert sorted(BY_HANDLE) == sorted(h for c in CATS.values() for h in c["handles"]), "every real product in exactly one category"
def variants(p): return [CAT["variants"][str(v)] for v in p["variants"]]
def money(c): return f"${c/100:.2f}"
def from_price(key):
    ps = [v["price"] for h in CATS[key]["handles"] for v in variants(BY_HANDLE[h])]
    return money(min(ps))
REVIEWS = [  # the 5 real Judge.me reviews shown on tresora.store (5.00 average)
  ("Bought this as a gift for a wine lover.. The presentation is gorgeous, everything feels high quality and thoughtfully put together. Shipping was fast too. Thank you!", "Anonymous", "Caravaggio Bacchus Wine Gift Box"),
  ("Absolutely love this set. I gave it to my mom as a gift. Her favorite is the tea cup with the butterfly and roses. It’s so pretty.", "SueD", "Klimt The Kiss Gift Box"),
  ("I gave it to my mom. She really liked it. Thank you.👌", "Anonymous", "Klimt The Kiss Gift Box"),
  ("I gave it to my mom. She really liked it. Thank you very much.", "Anonymous", "TRESORA"),
  ("Bought this as a gift for a wine lover.. The presentation is gorgeous, everything feels high quality and thoughtfully put together. Shipping was fast too. Thank you!", "Anonymous", "TRESORA"),
]
WHY = [("Curated, not generic.", "Every box tells a story."), ("Inspired by Art & Places.", "Discover a city, artist or moment through objects."),
       ("Ready to gift.", "Beautifully packaged and ready to give."), ("Made to be remembered.", "Not another gift that gets forgotten.")]
POL = "https://tresora.store/policies/"
ICON = {
 "search": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
 "user": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>',
 "bag": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 8h14l-1 13H6L5 8Z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/></svg>',
 "menu": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
 "lock": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
 "truck": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>',
 "gift": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="9" width="18" height="12" rx="1"/><path d="M3 13h18M12 9v12M12 9c-2-4-6-4-6-1.5S9 9 12 9Zm0 0c2-4 6-4 6-1.5S15 9 12 9Z"/></svg>',
 "return": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9h11a5 5 0 0 1 0 10H8"/><path d="m8 5-4 4 4 4"/></svg>',
 "star": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
 "mail": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
}
TRUST = [("lock", "Secure checkout", "Payments processed by Stripe. We never see your card."),
         ("truck", "Free US shipping", "On all orders, shipped from Los Angeles."),
         ("gift", "Gift-ready", "Every box arrives beautifully packaged."),
         ("return", "Returns & refunds", "Clear policy, see our Refund policy.")]

def stars(n=5): return '<span class="rd-stars" aria-label="5 out of 5 stars">' + ICON["star"] * n + "</span>"

def card(p, cat_key, big=False):
    vs = variants(p); v0 = vs[0]; avail = any(v["available"] for v in vs)
    href = f'{B}products/{p["handle"]}.html'
    opts = ""
    if len(vs) > 1:
        opts = '<label class="rd-card__opt"><span class="rd-sr">Color</span><select data-rd-variant aria-label="Color">' + "".join(
            f'<option value="{v["id"]}" data-img="{B}{E(v["image"])}" data-price="{money(v["price"])}"{"" if v["available"] else " disabled"}>{E(v["variant_title"])}</option>' for v in vs) + "</select></label>"
    btn = (f'<button class="rd-btn rd-btn--add" type="button" data-rd-add="{v0["id"]}">Add to cart</button>' if avail
           else '<button class="rd-btn rd-btn--add" type="button" disabled>Sold out</button>')
    badge = "" if avail else '<span class="rd-badge">Sold out</span>'
    return f'''<article class="rd-card" data-cat="{cat_key}" data-title="{E(p["title"].lower())}">
  <a class="rd-card__media" href="{href}">{badge}<img src="{B}{E(v0["image"])}" alt="{E(p["title"])}" width="800" height="800" loading="lazy" decoding="async" data-rd-img></a>
  <div class="rd-card__body">
    <p class="rd-card__cat">{E(CATS[cat_key]["short"])}</p>
    <h3 class="rd-card__title"><a href="{href}">{E(p["title"])}</a></h3>
    <p class="rd-card__price" data-rd-price>{money(v0["price"])}</p>
    <div class="rd-card__buy">{opts}{btn}</div>
  </div>
</article>'''

def grid(cols_class=""):
    cards = "".join(card(BY_HANDLE[h], k) for k, c in CATS.items() for h in c["handles"])
    tabs = '<button class="rd-tab" type="button" data-rd-filter="all" aria-pressed="true">All <span>12</span></button>' + "".join(
        f'<button class="rd-tab" type="button" data-rd-filter="{k}" aria-pressed="false">{E(c["short"])} <span>{len(c["handles"])}</span></button>' for k, c in CATS.items())
    return f'''<div class="rd-shopbar"><div class="rd-tabs" role="toolbar" aria-label="Filter by category">{tabs}</div>
  <p class="rd-shopbar__note" data-rd-result>12 products</p></div>
<div class="rd-grid {cols_class}" data-rd-grid>{cards}</div>
<p class="rd-empty" data-rd-noresult hidden>No products match your search. <button class="rd-linkbtn" type="button" data-rd-clear>Show all products</button></p>'''

def cat_tiles():
    return '<div class="rd-cats">' + "".join(f'''<a class="rd-cat" href="#shop" data-rd-goto="{k}">
  <img src="{c["img"]}" alt="" width="800" height="800" loading="lazy" decoding="async">
  <span class="rd-cat__text"><strong>{E(c["name"])}</strong><em>{E(c["blurb"])}</em><small>{len(c["handles"])} products · from {from_price(k)}</small></span></a>''' for k, c in CATS.items()) + "</div>"

def trust(cls=""):
    return f'<ul class="rd-trust {cls}">' + "".join(f'<li>{ICON[i]}<div><strong>{t}</strong><span>{d}</span></div></li>' for i, t, d in TRUST) + "</ul>"

def reviews():
    items = "".join(f'''<figure class="rd-review">{stars()}<blockquote>{E(t)}</blockquote>
  <figcaption><strong>{E(n)}</strong><span>{E(pr)}</span></figcaption></figure>''' for t, n, pr in REVIEWS)
    photos = f'''<div class="rd-review-photos"><img src="{IMG}1788968950__img_2017__original-w1024-a11738.jpeg" alt="Customer photo of the Caravaggio Bacchus Wine Gift Box" loading="lazy" width="1024" height="1365">
<img src="{IMG}1791484389__img_2259__original-w1024-300637.jpeg" alt="Customer photo of a TRESORA gift box" loading="lazy" width="497" height="661"></div>'''
    return f'''<div class="rd-reviews__head"><div class="rd-score"><b>5.00</b>{stars()}<span>Based on 5 verified reviews</span></div></div>
<div class="rd-reviews__body">{photos}<div class="rd-reviews__list">{items}</div></div>'''

def why():
    return '<ol class="rd-why">' + "".join(f"<li><strong>{E(a)}</strong><span>{E(b)}</span></li>" for a, b in WHY) + "</ol>"

def newsletter(title="Quiet updates. New collections. Nothing more.", sub="Join the TRESORA list for new boxes and early access. Unsubscribe anytime."):
    return f'''<form class="rd-news" data-rd-news novalidate>
  <div class="rd-news__text"><h2>{E(title)}</h2><p>{E(sub)}</p></div>
  <div class="rd-news__form"><label class="rd-sr" for="rd-news-email">Email address</label>
    <input id="rd-news-email" type="email" name="email" placeholder="Your email address" autocomplete="email" required>
    <button class="rd-btn" type="submit">Subscribe</button></div>
  <label class="rd-news__consent"><input type="checkbox" name="consent" required> I agree to receive emails from TRESORA.</label>
  <p class="rd-news__msg" data-rd-msg role="status" aria-live="polite"></p>
</form>'''

def header(variant):
    nav = "".join(f'<a href="#shop" data-rd-goto="{k}">{E(c["name"])}</a>' for k, c in CATS.items())
    return f'''<div class="rd-announce"><span>Free US shipping on all orders</span><span class="rd-dot">·</span><span>Secure checkout via Stripe</span><span class="rd-dot rd-hide-sm">·</span><span class="rd-hide-sm">Gift-ready packaging</span></div>
<header class="rd-header" data-rd-header>
  <div class="rd-header__in">
    <button class="rd-icon rd-menu-btn" type="button" data-rd-menu aria-expanded="false" aria-controls="rd-nav" aria-label="Menu">{ICON["menu"]}</button>
    <a class="rd-logo" href="./" aria-label="TRESORA home"><img src="{IMG}25d07e5ce9255cb0bd9e82c85fc13b9d-h100-61ae14.png" alt="TRESORA" width="150" height="100"></a>
    <nav class="rd-nav" id="rd-nav" aria-label="Main"><a href="#shop" data-rd-goto="all">Shop all</a>{nav}<a href="#reviews">Reviews</a></nav>
    <form class="rd-search" role="search" data-rd-search>
      <label class="rd-sr" for="rd-q">Search products</label>
      {ICON["search"]}<input id="rd-q" type="search" placeholder="Search gift boxes, cities, artists…" autocomplete="off" data-rd-q aria-controls="rd-suggest" aria-expanded="false">
      <div class="rd-suggest" id="rd-suggest" role="listbox" data-rd-suggest hidden></div>
    </form>
    <div class="rd-actions">
      <button class="rd-icon rd-search-btn" type="button" data-rd-searchtoggle aria-label="Search">{ICON["search"]}</button>
      <button class="rd-icon rd-account" type="button" data-rd-account="signin" aria-label="Account">{ICON["user"]}<span class="rd-hide-sm">Sign in</span></button>
      <button class="rd-icon rd-cart" type="button" data-cart-open aria-label="Cart">{ICON["bag"]}<span class="rd-count" data-cart-count hidden>0</span></button>
    </div>
  </div>
</header>'''

def footer():
    return f'''<footer class="rd-footer">
  <div class="rd-footer__top">
    <div class="rd-footer__brand"><img src="{IMG}25d07e5ce9255cb0bd9e82c85fc13b9d-h100-61ae14.png" alt="TRESORA" width="150" height="100" loading="lazy">
      <p>Gift boxes inspired by art, cities, and beautiful moments. Curated with intention. Made to be remembered.</p>
      <p class="rd-social"><a href="#">Instagram</a><a href="#">Facebook</a><a href="#">TikTok</a><a href="#">Pinterest</a><a href="#">Etsy</a></p></div>
    <div><h3>Shop</h3><a href="#shop" data-rd-goto="all">All products</a>{"".join(f'<a href="#shop" data-rd-goto="{k}">{E(c["name"])}</a>' for k, c in CATS.items())}</div>
    <div><h3>Client care</h3><a href="{POL}contact-information">Contact us</a><a href="{POL}shipping-policy">Shipping</a><a href="{POL}refund-policy">Returns &amp; refunds</a><a href="#reviews">Reviews</a></div>
    <div><h3>Account</h3><button type="button" class="rd-linkbtn" data-rd-account="signin">Sign in</button><button type="button" class="rd-linkbtn" data-rd-account="signup">Create account</button><button type="button" class="rd-linkbtn" data-cart-open>View cart</button></div>
  </div>
  <div class="rd-footer__bottom">
    <p>© 2026 TRESORA</p>
    <p class="rd-pay">{ICON["lock"]} Secure payments by Stripe · Visa · Mastercard · Amex · Apple Pay · Google Pay</p>
    <p class="rd-policies"><a href="{POL}privacy-policy">Privacy policy</a><a href="{POL}refund-policy">Refund policy</a><a href="{POL}terms-of-service">Terms of service</a><a href="{POL}shipping-policy">Shipping policy</a></p>
  </div>
</footer>'''

MODAL = '''<dialog class="rd-modal" data-rd-modal aria-labelledby="rd-modal-title">
  <form method="dialog" class="rd-modal__close"><button aria-label="Close">×</button></form>
  <h2 id="rd-modal-title" data-rd-modal-title>Welcome back</h2>
  <div class="rd-modal__tabs" role="tablist"><button type="button" role="tab" data-rd-tab="signin" aria-selected="true">Sign in</button><button type="button" role="tab" data-rd-tab="signup" aria-selected="false">Create account</button></div>
  <form class="rd-auth" data-rd-auth novalidate>
    <label data-only="signup">Name<input name="name" autocomplete="name"></label>
    <label>Email<input name="email" type="email" autocomplete="email" required></label>
    <label>Password<span class="rd-pass"><input name="password" type="password" autocomplete="current-password" minlength="8" required><button type="button" class="rd-linkbtn" data-rd-showpass>Show</button></span></label>
    <label class="rd-check" data-only="signup"><input type="checkbox" name="news"> Email me new collections</label>
    <button class="rd-btn rd-btn--full" type="submit" data-rd-submit>Sign in</button>
    <button type="button" class="rd-linkbtn rd-forgot" data-only="signin" data-rd-forgot>Forgot password?</button>
    <p class="rd-auth__msg" data-rd-msg role="status" aria-live="polite"></p>
    <p class="rd-auth__note">Preview: accounts are not live yet. Nothing you type here is sent or stored.</p>
  </form>
</dialog>'''

def page(n, title, body, theme_color):
    return f'''<!doctype html>
<html lang="en" data-base="{B}" class="rd rd-v{n}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="Art and city inspired gift boxes. Free US shipping. Secure checkout via Stripe.">
<meta name="theme-color" content="{theme_color}"><meta name="robots" content="noindex">
<link rel="icon" href="{IMG}favicon.png">
<link rel="stylesheet" href="{B}assets/css/shop.css"><link rel="stylesheet" href="../shared/base.css"><link rel="stylesheet" href="style.css">
</head><body>
<a class="rd-skip" href="#main">Skip to content</a>
{header(n)}
<main id="main">{body}</main>
{footer()}
{MODAL}
<script src="{B}assets/js/config.js"></script><script src="{B}assets/js/catalog.js"></script><script src="{B}assets/js/payment-links.js"></script><script src="{B}assets/js/cart.js"></script>
<script src="../shared/rd.js"></script>
</body></html>'''

HERO_IMG = "../shared/hero-box.jpg"   # 1024x1440: the store's hero photo with Shopify's "Made with AI" label cropped off the top
HERO_WIDE = IMG + "Screenshot_2026-09-12_at_3.44.55_pm-w800-ed034c.png"

# ---------------- v1 Luxury dark (navy / emerald / ivory, no gold) ----------------
v1 = f'''
<section class="rd-hero">
  <div class="rd-hero__media"><img src="{HERO_IMG}" alt="Black TRESORA gift box tied with an ivory satin ribbon on tulle" width="1024" height="1440" fetchpriority="high"></div>
  <div class="rd-hero__text">
    <p class="rd-eyebrow">Art &amp; city inspired gift boxes</p>
    <h1>Give the moment.<br><em>Keep the feeling.</em></h1>
    <p class="rd-lead">Curated gift boxes inspired by Klimt, Vermeer, Paris and Barcelona. Beautifully packaged, ready to give, with free US shipping.</p>
    <div class="rd-cta"><a class="rd-btn rd-btn--light" href="#shop" data-rd-goto="all">Shop gift boxes</a><a class="rd-btn rd-btn--ghost" href="#categories">Explore collections</a></div>
    <p class="rd-hero__proof">{stars()} <span>5.00 · 5 reviews</span></p>
  </div>
</section>
{trust("rd-trust--band")}
<section class="rd-section" id="categories"><header class="rd-head"><p class="rd-eyebrow">Collections</p><h2>Find your TRESORA</h2></header>{cat_tiles()}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head"><p class="rd-eyebrow">The boutique</p><h2>All gift boxes &amp; objects</h2></header>{grid()}</section>
<section class="rd-section rd-story"><div class="rd-story__img"><img src="{HERO_WIDE}" alt="TRESORA Barcelona gift box with a mosaic hand fan on a sunlit terrace" loading="lazy" width="800" height="801"></div>
  <div class="rd-story__text"><p class="rd-eyebrow">Why TRESORA</p><h2>Gifts with a story inside</h2>{why()}</div></section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head"><p class="rd-eyebrow">Reviews</p><h2>Loved by the people who receive them</h2></header>{reviews()}</section>
<section class="rd-section rd-section--news">{newsletter()}</section>'''

# ---------------- v2 Warm gallery (burgundy / terracotta / cream) ----------------
def gallery_room(k):
    c = CATS[k]
    return f'''<section class="rd-room" id="room-{k}"><header class="rd-room__head"><p class="rd-label">Room {list(CATS).index(k)+1}</p><h2>{E(c["name"])}</h2><p>{E(c["blurb"])}</p>
  <a class="rd-linkbtn" href="#shop" data-rd-goto="{k}">See all {len(c["handles"])} →</a></header></section>'''
v2 = f'''
<section class="rd-hero">
  <div class="rd-hero__text">
    <p class="rd-label">Exhibition No. 1 · Art &amp; Places</p>
    <h1>Gifts curated like a gallery.</h1>
    <p class="rd-lead">Each TRESORA box is inspired by a painting or a city: Klimt’s The Kiss, Vermeer’s Girl with a Pearl Earring, the light of Paris, the color of Barcelona.</p>
    <div class="rd-cta"><a class="rd-btn" href="#shop" data-rd-goto="all">Visit the collection</a><a class="rd-btn rd-btn--outline" href="#reviews">Read reviews · 5.00</a></div>
  </div>
  <figure class="rd-hero__frame"><img src="{HERO_IMG}" alt="Black TRESORA gift box tied with an ivory satin ribbon" width="1024" height="1440" fetchpriority="high">
    <figcaption><strong>The TRESORA Box</strong><span>Beautifully packaged and ready to give · ships free across the US from Los Angeles</span></figcaption></figure>
</section>
<section class="rd-section rd-section--trust">{trust()}</section>
<section class="rd-section" id="categories"><header class="rd-head"><p class="rd-label">The rooms</p><h2>Choose your wing</h2></header>{cat_tiles()}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head"><p class="rd-label">Catalogue</p><h2>The collection</h2><p>Every piece with its price. Add to cart directly, or open a box to see what’s inside.</p></header>{grid("rd-grid--gallery")}</section>
<section class="rd-section rd-why-wrap"><header class="rd-head"><p class="rd-label">Curator’s note</p><h2>Why TRESORA</h2></header>{why()}</section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head"><p class="rd-label">Guest book</p><h2>What our visitors say</h2></header>{reviews()}</section>
<section class="rd-section rd-section--news">{newsletter("Be first at the next opening.", "New boxes and limited editions, a few times a year. Unsubscribe anytime.")}</section>'''

# ---------------- v3 Modern clean shop (white + cobalt) ----------------
v3 = f'''
<section class="rd-hero">
  <div class="rd-hero__main">
    <div class="rd-hero__text"><p class="rd-pill">New · City collection</p>
      <h1>Thoughtful gift boxes, ready to ship.</h1>
      <p class="rd-lead">12 curated boxes and handmade objects inspired by art and cities. Free US shipping, secure Stripe checkout.</p>
      <div class="rd-cta"><a class="rd-btn" href="#shop" data-rd-goto="all">Shop all products</a><a class="rd-btn rd-btn--outline" href="#shop" data-rd-goto="city">City boxes from {from_price("city")}</a></div>
      <p class="rd-hero__proof">{stars()} <span><b>5.00</b> from 5 reviews</span></p></div>
    <img class="rd-hero__img" src="{HERO_IMG}" alt="Black TRESORA gift box with ivory ribbon" width="1024" height="1440" fetchpriority="high">
  </div>
  <div class="rd-hero__side">{"".join(f'<a class="rd-promo" href="#shop" data-rd-goto="{k}"><img src="{c["img"]}" alt="" width="800" height="800"><span><strong>{E(c["name"])}</strong><small>{len(c["handles"])} products · from {from_price(k)}</small></span></a>' for k, c in list(CATS.items())[:2])}</div>
</section>
<section class="rd-section rd-section--trust">{trust()}</section>
<section class="rd-section" id="categories"><header class="rd-head rd-head--row"><h2>Shop by category</h2></header>{cat_tiles()}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head rd-head--row"><h2>All products</h2></header>{grid("rd-grid--dense")}</section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head rd-head--row"><h2>Customer reviews</h2></header>{reviews()}</section>
<section class="rd-section rd-why-wrap"><header class="rd-head rd-head--row"><h2>Why shop with TRESORA</h2></header>{why()}</section>
<section class="rd-section rd-section--news">{newsletter("Get the first look at new boxes", "One short email when a new collection drops. No spam, unsubscribe anytime.")}</section>'''

for n, body, title, tc in [(1, v1, "TRESORA · Concept 1 · Luxury dark", "#0f1b2d"), (2, v2, "TRESORA · Concept 2 · Warm gallery", "#6b1f2a"), (3, v3, "TRESORA · Concept 3 · Modern clean shop", "#ffffff")]:
    os.makedirs(f"redesign/v{n}", exist_ok=True)
    open(f"redesign/v{n}/index.html", "w", encoding="utf-8").write(page(n, title, body, tc))
print("built redesign/v1..v3")
