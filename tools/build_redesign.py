"""Build 3 complete mini-site design concepts in redesign/v1..v3 from the real catalog.
Each concept: index.html, shop.html (filters + sort), products/<handle>.html (all 12), cart.html, account.html.
Nothing on the live site is touched. usage: python3 tools/build_redesign.py"""
import json, html, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
s = open("assets/js/catalog.js").read()
CAT = json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])
RAW = {p["handle"]: p for p in json.load(open("orig/products.json"))["products"]}   # real Shopify product data (body_html, images, options)
SIZES = json.load(open("redesign/shared/products/sizes.json"))
R = "/tresora-clone/"                 # site root on GitHub Pages and on the local test server
SH = R + "redesign/shared/"
IMG = R + "assets/images/"
E = html.escape
V = ""                                # current concept root, set per concept below
N = 0
CATS = {
  "art":  {"name": "Inspired by Art", "short": "Art", "img": SH + "img/cat-art.jpg",
           "blurb": "Klimt, Vermeer, Van Gogh, Caravaggio and Sargent, translated into objects.",
           "handles": ["caravaggio-bacchus-wine-gift-box", "vermeer-girl-with-a-pearl-earring-gift-box", "klimt-the-kiss-gift-box",
                       "van-gogh-almond-blossom-gift-box", "sargent-the-wineglasses-wine-gift-box", "elegant-pearl-earring-table-gift-box"]},
  "city": {"name": "Inspired by City", "short": "City", "img": SH + "img/cat-city.jpg",
           "blurb": "Every city has a feeling. We turn it into a gift.",
           "handles": ["paris-gift-box", "barcelona-gift-box", "new-york-gift-box", "amalfi-gift-box"]},
  "home": {"name": "Atelier Home", "short": "Atelier Home", "img": SH + "img/cat-home.jpg",
           "blurb": "Handmade objects for a beautiful home.",
           "handles": ["gothic-romance-decorative-glass-bottle", "rococo-reverie-decorative-glass-bottle"]},
}
BY_HANDLE = {p["handle"]: p for p in CAT["products"].values()}
assert sorted(BY_HANDLE) == sorted(h for c in CATS.values() for h in c["handles"]), "every real product in exactly one category"
CAT_OF = {h: k for k, c in CATS.items() for h in c["handles"]}
ORDER = [h for c in CATS.values() for h in c["handles"]]
def variants(p): return [CAT["variants"][str(v)] for v in p["variants"]]
def money(c): return f"${c/100:.2f}"
def from_price(key): return money(min(v["price"] for h in CATS[key]["handles"] for v in variants(BY_HANDLE[h])))
def purl(h): return f"{V}products/{h}.html"
VKEY = {"caravaggio-bacchus-wine-gift-box": {"Green": "green", "Red": "red"}, "vermeer-girl-with-a-pearl-earring-gift-box": {"Light Blue": "light-blue", "White": "white"}}
def lead(h, v=None):
    k = h if h not in VKEY else f"{h}-{VKEY[h][(v or variants(BY_HANDLE[h])[0])['variant_title']]}"
    return f"{SH}products/{k}-lead.jpg", f"{SH}products/{k}-lead-t.jpg"
PACK = {"amalfi-gift-box": [9, 10], "barcelona-gift-box": [0, 10, 11], "caravaggio-bacchus-wine-gift-box": [1, 2, 5, 8], "elegant-pearl-earring-table-gift-box": [3, 4, 5, 6],
        "gothic-romance-decorative-glass-bottle": [3, 4], "klimt-the-kiss-gift-box": [2, 6, 7], "new-york-gift-box": [9, 10], "paris-gift-box": [8],
        "sargent-the-wineglasses-wine-gift-box": [2, 3, 5], "van-gogh-almond-blossom-gift-box": [3, 4, 6], "vermeer-girl-with-a-pearl-earring-gift-box": [3, 4, 7, 8]}
LEAD_SAME = {"amalfi-gift-box": 2, "barcelona-gift-box": 2, "new-york-gift-box": 1, "paris-gift-box": 2, "klimt-the-kiss-gift-box": 1,
             "van-gogh-almond-blossom-gift-box": 5, "gothic-romance-decorative-glass-bottle": 0, "rococo-reverie-decorative-glass-bottle": 0}  # lead = this photo, don't repeat it
def gallery(h):
    """lead (items) first, then item shots, packaging / personalisation shots last"""
    n = len(RAW[h]["images"]); order = [i for i in range(n) if i not in PACK.get(h, []) and i != LEAD_SAME.get(h)] + [i for i in PACK.get(h, []) if i < n]
    big, t = lead(h)
    return [(big, t, 1200, 900)] + [(f"{SH}products/{h}-{i}.jpg", f"{SH}products/{h}-{i}-t.jpg", SIZES[f"{h}-{i}"][2], SIZES[f"{h}-{i}"][3]) for i in order]
REVIEWS = [  # the 5 real Judge.me reviews shown on tresora.store (5.00 average)
  ("Bought this as a gift for a wine lover.. The presentation is gorgeous, everything feels high quality and thoughtfully put together. Shipping was fast too. Thank you!", "Anonymous", "Caravaggio Bacchus Wine Gift Box"),
  ("Absolutely love this set. I gave it to my mom as a gift. Her favorite is the tea cup with the butterfly and roses. It’s so pretty.", "SueD", "Klimt The Kiss Gift Box"),
  ("I gave it to my mom. She really liked it. Thank you.👌", "Anonymous", "Klimt The Kiss Gift Box"),
  ("I gave it to my mom. She really liked it. Thank you very much.", "Anonymous", "TRESORA"),
  ("Bought this as a gift for a wine lover.. The presentation is gorgeous, everything feels high quality and thoughtfully put together. Shipping was fast too. Thank you!", "Anonymous", "TRESORA"),
]
WHY = [("Curated, not generic.", "Every piece tells a story."), ("Inspired by Art & Places.", "Discover a city, artist or moment through objects."),
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
         ("gift", "Ready to give", "Arrives beautifully wrapped, with a card."),
         ("return", "Returns & refunds", "Clear policy, see our Refund policy.")]


def stars(n=5): return '<span class="rd-stars" aria-label="5 out of 5 stars">' + ICON["star"] * n + "</span>"

def card(p, cat_key):
    vs = variants(p); v0 = vs[0]; avail = any(v["available"] for v in vs); href = purl(p["handle"])
    opts = ""
    if len(vs) > 1:
        opts = '<label class="rd-card__opt"><span class="rd-sr">Color</span><select data-rd-variant aria-label="Color">' + "".join(
            f'<option value="{v["id"]}" data-img="{lead(p["handle"], v)[0]}" data-price="{money(v["price"])}"{"" if v["available"] else " disabled"}>{E(v["variant_title"])}</option>' for v in vs) + "</select></label>"
    btn = (f'<button class="rd-btn rd-btn--add" type="button" data-rd-add="{v0["id"]}">Add to cart</button>' if avail
           else '<button class="rd-btn rd-btn--add" type="button" disabled>Sold out</button>')
    badge = "" if avail else '<span class="rd-badge">Sold out</span>'
    note = f'<span class="rd-card__note">{len(vs)} colors</span>' if len(vs) > 1 else ""
    return f'''<article class="rd-card" data-rd-buy data-cat="{cat_key}" data-title="{E(p["title"].lower())}" data-price="{v0["price"]}" data-order="{ORDER.index(p["handle"])}" data-avail="{int(avail)}">
  <a class="rd-card__media" href="{href}">{badge}<img src="{lead(p["handle"])[0]}" alt="{E(p["title"])}" width="1200" height="900" loading="lazy" decoding="async" data-rd-img></a>
  <div class="rd-card__body">
    <p class="rd-card__cat">{E(CATS[cat_key]["short"])}</p>
    <h3 class="rd-card__title"><a href="{href}">{E(p["title"])}</a></h3>
    <p class="rd-card__inside">{E(inside_line(p["handle"]))}</p>
    <p class="rd-card__price"><span data-rd-price>{money(v0["price"])}</span>{note}</p>
    <div class="rd-card__buy">{opts}{btn}</div>
  </div>
</article>'''

def tabs():
    return ('<button class="rd-tab" type="button" data-rd-filter="all" aria-pressed="true">All <span>12</span></button>' + "".join(
        f'<button class="rd-tab" type="button" data-rd-filter="{k}" aria-pressed="false">{E(c["short"])} <span>{len(c["handles"])}</span></button>' for k, c in CATS.items()))

def grid(cols_class="", tools=False, handles=None):
    hs = handles or ORDER
    cards = "".join(card(BY_HANDLE[h], CAT_OF[h]) for h in hs)
    extra = ""
    if tools:
        extra = '''<div class="rd-shoptools"><label class="rd-check"><input type="checkbox" data-rd-instock> In stock only</label>
    <label class="rd-sort"><span>Sort</span><select data-rd-sort aria-label="Sort products"><option value="featured">Featured</option><option value="price-asc">Price, low to high</option><option value="price-desc">Price, high to low</option><option value="az">Alphabetically, A–Z</option></select></label></div>'''
    return f'''<div class="rd-shopbar"><div class="rd-tabs" role="toolbar" aria-label="Filter by category">{tabs()}</div>{extra}
  <p class="rd-shopbar__note" data-rd-result>{len(hs)} products</p></div>
<div class="rd-grid {cols_class}" data-rd-grid>{cards}</div>
<p class="rd-empty" data-rd-noresult hidden>No products match. <button class="rd-linkbtn" type="button" data-rd-clear>Show all products</button></p>'''

def cat_tiles(art_img=None):
    def img(k): return art_img if (k == "art" and art_img) else CATS[k]["img"]
    return '<div class="rd-cats">' + "".join(f'''<a class="rd-cat" href="{V}shop.html?cat={k}">
  <span class="rd-cat__media"><img src="{img(k)}" alt="" width="900" height="1125" loading="lazy" decoding="async"></span>
  <span class="rd-cat__text"><small>{i+1:02d} · {len(c["handles"])} pieces · from {from_price(k)}</small><strong>{E(c["name"])}</strong><em>{E(c["blurb"])}</em><span class="rd-more">Discover</span></span></a>''' for i, (k, c) in enumerate(CATS.items())) + "</div>"

def trust(cls=""):
    return f'<ul class="rd-trust {cls}">' + "".join(f'<li>{ICON[i]}<div><strong>{t}</strong><span>{d}</span></div></li>' for i, t, d in TRUST) + "</ul>"

def review_items(rs):
    return "".join(f'''<figure class="rd-review">{stars()}<blockquote>{E(t)}</blockquote>
  <figcaption><strong>{E(n)}</strong><span>{E(pr)}</span></figcaption></figure>''' for t, n, pr in rs)

def reviews():
    return f'''<div class="rd-reviews__head"><div class="rd-score"><b>5.00</b>{stars()}<span>Based on 5 verified reviews</span></div></div>
<div class="rd-reviews__body rd-reviews__body--text"><div class="rd-reviews__list">{review_items(REVIEWS)}</div></div>'''

def why():
    return '<ol class="rd-why">' + "".join(f"<li><strong>{E(a)}</strong><span>{E(b)}</span></li>" for a, b in WHY) + "</ol>"

def newsletter(title="Quiet updates. New collections. Nothing more.", sub="Join the TRESORA list for new collections and early access. Unsubscribe anytime."):
    return f'''<form class="rd-news" data-rd-news novalidate>
  <div class="rd-news__text"><h2>{E(title)}</h2><p>{E(sub)}</p></div>
  <div class="rd-news__form"><label class="rd-sr" for="rd-news-email">Email address</label>
    <input id="rd-news-email" type="email" name="email" placeholder="Email address" autocomplete="email" required>
    <button class="rd-btn rd-btn--primary" type="submit">Subscribe</button></div>
  <label class="rd-news__consent"><input type="checkbox" name="consent" required> I agree to receive emails from TRESORA.</label>
  <p class="rd-news__msg" data-rd-msg role="status" aria-live="polite"></p>
</form>'''

def header(active=""):
    def cls(k): return ' aria-current="page"' if k == active else ""
    nav = "".join(f'<a href="{V}shop.html?cat={k}">{E(c["name"])}</a>' for k, c in CATS.items())
    return f'''<div class="rd-announce"><span>Complimentary US shipping on every order</span><span class="rd-dot rd-hide-sm"></span><span class="rd-hide-sm">Secure checkout via Stripe</span></div>
<header class="rd-header" data-rd-header>
  <div class="rd-header__in">
    <button class="rd-icon rd-menu-btn" type="button" data-rd-menu aria-expanded="false" aria-controls="rd-nav" aria-label="Menu">{ICON["menu"]}</button>
    <a class="rd-logo" href="{V}" aria-label="TRESORA home"><img src="{SH}img/logo-{"light" if N == 1 else "dark"}.png" alt="TRESORA" width="706" height="497"></a>
    <nav class="rd-nav" id="rd-nav" aria-label="Main"><a href="{V}shop.html"{cls("shop")}>Shop all</a>{nav}<a href="{V}#reviews">Reviews</a><a class="rd-nav__acc" href="{V}account.html">Account</a></nav>
    <form class="rd-search" role="search" data-rd-search action="{V}shop.html">
      <label class="rd-sr" for="rd-q">Search products</label>
      {ICON["search"]}<input id="rd-q" name="q" type="search" placeholder="Search" autocomplete="off" data-rd-q aria-controls="rd-suggest" aria-expanded="false">
      <div class="rd-suggest" id="rd-suggest" role="listbox" data-rd-suggest hidden></div>
    </form>
    <div class="rd-actions">
      <button class="rd-icon rd-search-btn" type="button" data-rd-searchtoggle aria-label="Search">{ICON["search"]}</button>
      <a class="rd-icon rd-account" href="{V}account.html" data-rd-account aria-label="Account"{cls("account")}>{ICON["user"]}<span class="rd-hide-sm">Account</span></a>
      <button class="rd-icon rd-cart" type="button" data-cart-open aria-label="Cart">{ICON["bag"]}<span class="rd-count" data-cart-count hidden>0</span></button>
    </div>
  </div>
</header>'''

def footer():
    return f'''<footer class="rd-footer">
  <div class="rd-footer__top">
    <div class="rd-footer__brand"><img src="{SH}img/logo-light.png" alt="TRESORA" width="706" height="497" loading="lazy">
      <p>Gifts inspired by art, cities, and beautiful moments. Curated with intention. Made to be remembered.</p>
      <p class="rd-social"><a href="#">Instagram</a><a href="#">Facebook</a><a href="#">TikTok</a><a href="#">Pinterest</a><a href="#">Etsy</a></p></div>
    <div><h3>Shop</h3><a href="{V}shop.html">All products</a>{"".join(f'<a href="{V}shop.html?cat={k}">{E(c["name"])}</a>' for k, c in CATS.items())}</div>
    <div><h3>Client care</h3><a href="{POL}contact-information">Contact us</a><a href="{POL}shipping-policy">Shipping</a><a href="{POL}refund-policy">Returns &amp; refunds</a><a href="{V}#reviews">Reviews</a></div>
    <div><h3>Account</h3><a href="{V}account.html">Sign in</a><a href="{V}account.html?mode=signup">Create account</a><a href="{V}cart.html">Your cart</a></div>
  </div>
  <div class="rd-footer__bottom">
    <p>© 2026 TRESORA</p>
    <p class="rd-pay">{ICON["lock"]} Secure payments by Stripe · Visa · Mastercard · Amex · Apple Pay · Google Pay</p>
    <p class="rd-policies"><a href="{POL}privacy-policy">Privacy policy</a><a href="{POL}refund-policy">Refund policy</a><a href="{POL}terms-of-service">Terms of service</a><a href="{POL}shipping-policy">Shipping policy</a></p>
  </div>
</footer>'''

def page(title, body, kind, active="", desc="Art-inspired and city-inspired gifts. Free US shipping. Secure checkout via Stripe."):
    tc = {1: "#0d1726", 2: "#f6efe4", 3: "#ffffff"}[N]
    return f'''<!doctype html>
<html lang="en" data-base="{R}" data-rd-root="{V}" class="rd rd-v{N} rd-page--{kind}{" rd-head-editorial" if N in (1, 2) else ""}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<meta name="theme-color" content="{tc}"><meta name="robots" content="noindex">
<link rel="icon" href="{IMG}favicon.png">
<link rel="stylesheet" href="{R}assets/css/shop.css"><link rel="stylesheet" href="{SH}base.css"><link rel="stylesheet" href="{V}style.css">
</head><body>
<a class="rd-skip" href="#main">Skip to content</a>
{header(active)}
<main id="main">{body}</main>
{footer()}
<script src="{R}assets/js/config.js"></script><script src="{R}assets/js/catalog.js"></script><script src="{R}assets/js/payment-links.js"></script><script src="{R}assets/js/cart.js"></script>
<script>window.RD_LEADS={json.dumps({str(v["id"]): list(lead(v["handle"], v)) for p in CAT["products"].values() for v in variants(p)}, separators=(",", ":"))};</script>
<script src="{SH}rd.js"></script>
</body></html>'''

def crumbs(*items):
    out = [f'<a href="{V}">Home</a>'] + [f'<a href="{h}">{E(t)}</a>' if h else f'<span aria-current="page">{E(t)}</span>' for t, h in items]
    return '<nav class="rd-crumbs" aria-label="Breadcrumb">' + '<span class="rd-crumbs__sep">/</span>'.join(out) + "</nav>"

# ---------------- product description: real body_html -> structured, classy markup ----------------
BULLET = re.compile(r"^\s*(✨|•|-|–|\*|✔️?|🌹|🍷|🎁|💌|⭐️?)\s*")
PACKWORDS = re.compile(r"gift box|packaging|presented in|presented gift-ready", re.I)
def parse(h):
    """real body_html -> tagline, intro paragraphs, inside items, packaging note, specs, remaining sections"""
    txt = re.sub(r"<meta[^>]*>", "", RAW[h]["body_html"])
    paras = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.split(r"</p>|<br\s*/?>|</li>|</h\d>", txt)]
    paras = [p for p in paras if p]
    first = re.sub(r"\s*[—–-]\s*boxed as .*$", ".", paras[0]).replace("..", ".")
    tagline, intro = (first, []) if (first.endswith(".") and len(first) < 90) else ("", [first] if first.endswith(".") else [])
    inside, pack, specs, rest = [], [], [], []
    mode = "intro"
    for p in paras[1:]:
        clean = BULLET.sub("", p).strip(); head = clean.rstrip(":").strip()
        is_head = (clean.isupper() and len(clean) < 40) or (clean.endswith(":") and len(clean) < 30)
        if is_head and re.match(r"what.?s inside|details", head, re.I): mode = "inside"; continue
        if is_head and re.search(r"packaging", head, re.I): mode = "pack"; continue
        if re.match(r"^LUXURY GIFT PACKAGING:?", clean): pack.append(re.sub(r"^LUXURY GIFT PACKAGING:?\s*", "", clean)); continue
        if is_head: mode = "rest"; rest.append(("h", head.title().replace("’S", "’s"))); continue
        if clean.startswith("Looking for"): continue          # links to a blog guide that the preview does not have
        if re.match(r"^(Perfect for|Care)\b", clean): mode = "rest"; rest.append(("p", clean)); continue
        if mode == "pack": pack.append(clean); mode = "rest"; continue
        if mode == "intro": intro.append(clean); continue
        if mode == "inside":
            if PACKWORDS.search(clean):
                if re.search(r"ready to give|presented", clean, re.I): pack.append(clean)
            elif clean.startswith("Size") and inside: inside[-1] += f" ({clean})"
            elif re.match(r"^(Dimensions|Materials)\b", clean): specs.append(clean)
            elif "(Dimensions:" in clean: x, y = clean.split("(Dimensions:", 1); inside.append(x.strip()); specs.append("Dimensions:" + y.rstrip(")"))
            elif clean.startswith(("Each ", "Personalized")) or p.startswith("💌"): rest.append(("p", clean))
            else: inside.append(clean)
        else: rest.append(("p", clean))
    return tagline, intro, inside, pack, specs, rest
def inside_line(h):
    tagline, intro, inside, pack, specs, rest = parse(h)
    if "gift-box" not in h:
        dim = next((x.split(":", 1)[1].split("×")[0].strip() for x in specs if x.startswith("Dimensions")), "")
        return "Hand-decorated glass · decoupage art" + (f" · {dim}" if dim else "")
    items = [re.split(r"\s+(?:—|\(|with\b|in a\b)", x)[0].strip().rstrip(".") for x in inside]
    short = [re.sub(r"^(Two|2)\s+", "2 ", x) for x in items[:3]]
    return " · ".join(short) + (f" · +{len(items) - 3} more" if len(items) > 3 else "")
def describe(h):
    tagline, intro, inside, pack, specs, rest = parse(h)
    more = "".join(f"<h3>{E(t)}</h3>" if k == "h" else f"<p>{E(t)}</p>" for k, t in rest if not (k == "h" and t.lower().startswith("keep this")))
    return tagline, intro, inside, pack, specs, more

def product_page(h):
    p = BY_HANDLE[h]; raw = RAW[h]; vs = variants(p); v0 = vs[0]; avail = any(v["available"] for v in vs); k = CAT_OF[h]
    gal = gallery(h)
    main_w, main_h = gal[0][2], gal[0][3]
    thumbs = "".join(f'<button type="button" class="rd-thumb" data-rd-thumb="{big}" aria-label="Show image {i+1}"{" aria-current=\"true\"" if i == 0 else ""}><img src="{t}" alt="" width="120" height="120" loading="lazy"></button>'
                     for i, (big, t, w, hh) in enumerate(gal))
    tagline, intro, inside, pack, specs, more = describe(h)
    is_set = "gift-box" in h
    inside_html = (f'''<div class="rd-inside" id="inside"><h2>{"What’s inside" if is_set else "The piece"}</h2><p class="rd-inside__count">{len(inside)} {"pieces" if is_set else "details"}</p>
      <ol>{"".join(f"<li>{E(x)}</li>" for x in inside)}</ol>{"".join(f'<p class="rd-inside__spec">{E(x)}</p>' for x in specs)}{"".join(f'<p class="rd-inside__pack">{ICON["gift"]} {E(x)}</p>' for x in pack)}</div>''')
    optname = raw["options"][0]["name"] if raw["options"] and raw["options"][0]["name"] != "Title" else "Option"
    pills = ""
    if len(vs) > 1:
        pills = f'<fieldset class="rd-pills"><legend>{E(optname)}: <b data-rd-optlabel>{E(v0["variant_title"])}</b></legend>' + "".join(
            f'<label><input type="radio" name="variant" value="{v["id"]}" data-img="{lead(h, v)[0]}" data-price="{money(v["price"])}" data-label="{E(v["variant_title"])}"{" checked" if i == 0 else ""}{"" if v["available"] else " disabled"}><span>{E(v["variant_title"])}</span></label>'
            for i, v in enumerate(vs)) + "</fieldset>"
    btn = (f'<button class="rd-btn rd-btn--primary rd-btn--full" type="button" data-rd-add="{v0["id"]}">Add to cart</button>' if avail
           else '<button class="rd-btn rd-btn--primary rd-btn--full" type="button" disabled>Sold out</button>')
    mine = [r for r in REVIEWS if r[2] == p["title"]]
    rev = (f'<section class="rd-section rd-pdp-reviews" id="reviews"><header class="rd-head"><p class="rd-eyebrow">Reviews</p><h2>What customers say about this box</h2></header><div class="rd-reviews__list">{review_items(mine)}</div></section>' if mine else "")
    related = [x for x in CATS[k]["handles"] if x != h][:4] or [x for x in ORDER if x != h][:4]
    body = f'''
<div class="rd-section rd-pdp-top">{crumbs(("Shop", V + "shop.html"), (CATS[k]["name"], f"{V}shop.html?cat={k}"), (p["title"], None))}</div>
<section class="rd-section rd-pdp" data-rd-buy data-rd-pdp>
  <div class="rd-pdp__gallery">
    <div class="rd-pdp__main">{"" if avail else '<span class="rd-badge">Sold out</span>'}<img src="{gal[0][0]}" alt="{E(p["title"])}" width="{main_w}" height="{main_h}" fetchpriority="high" data-rd-img data-rd-main></div>
    <div class="rd-thumbs" role="group" aria-label="Product images">{thumbs}</div>
  </div>
  <div class="rd-pdp__info">
    <p class="rd-eyebrow">{E(CATS[k]["name"])}</p>
    <h1>{E(p["title"])}</h1>
    <p class="rd-pdp__price"><span data-rd-price>{money(v0["price"])}</span> <small>USD · Free US shipping</small></p>
    {f'<p class="rd-pdp__tagline">{E(tagline)}</p>' if tagline else ""}
    {"".join(f'<p class="rd-pdp__intro">{E(x)}</p>' for x in intro)}
    <p class="rd-pdp__glance"><span>{"Inside" if is_set else "The piece"}</span> {E(inside_line(h))} <a href="#inside">{"See all " + str(len(inside)) if is_set else "Details"}</a></p>
    {pills}
    <div class="rd-pdp__buy"><div class="rd-qty"><button type="button" data-rd-step="-1" aria-label="Decrease quantity">−</button><input type="number" inputmode="numeric" min="1" max="10" value="1" data-rd-qty aria-label="Quantity"><button type="button" data-rd-step="1" aria-label="Increase quantity">+</button></div>{btn}</div>
    <ul class="rd-pdp__assure"><li>{ICON["lock"]} Secure checkout via Stripe</li><li>{ICON["truck"]} Free US shipping from Los Angeles</li><li>{ICON["gift"]} Arrives ready to give</li><li>{ICON["return"]} <a href="{POL}refund-policy">Returns &amp; refunds policy</a></li></ul>
    {inside_html}
    <div class="rd-pdp__desc">{more}</div>
  </div>
</section>
{rev}
<section class="rd-section rd-related"><header class="rd-head"><p class="rd-eyebrow">You may also like</p><h2>More from {E(CATS[k]["name"])}</h2></header><div class="rd-grid rd-grid--related">{"".join(card(BY_HANDLE[x], CAT_OF[x]) for x in related)}</div></section>'''
    return page(f"{p['title']} · TRESORA", body, "product", desc=(tagline + " " + (intro[0] if intro else ""))[:300])

def shop_page():
    body = f'''
<section class="rd-section rd-pagehead">{crumbs(("Shop", None))}<p class="rd-eyebrow">The collection</p><h1 data-rd-shoptitle>All gifts</h1>
  <p class="rd-lead">Tea cups and wine glasses after Klimt and Caravaggio, pearl bags and hand fans from Paris and Barcelona, handmade bottles for the home. Free US shipping on every order.</p></section>
<section class="rd-section rd-section--shop rd-shop" id="shop">{grid("rd-grid--shop", tools=True)}</section>
<section class="rd-section rd-section--trust">{trust()}</section>'''
    return page("Shop all · TRESORA", body, "shop", active="shop")

def cart_page():
    body = f'''
<section class="rd-section rd-pagehead">{crumbs(("Cart", None))}<h1>Your cart</h1></section>
<section class="rd-section rd-cartpage" data-rd-cartpage>
  <div class="rd-cartpage__list"><div class="rd-cartpage__cols" aria-hidden="true"><span>Product</span><span>Quantity</span><span>Total</span></div><ul data-rd-cartlines></ul>
    <div class="rd-cartpage__empty" data-rd-cartempty hidden><p>Your cart is empty.</p><a class="rd-btn rd-btn--primary" href="{V}shop.html">Continue shopping</a></div></div>
  <aside class="rd-summary" data-rd-summary>
    <h2>Order summary</h2>
    <dl><div><dt>Subtotal</dt><dd data-rd-subtotal>$0.00</dd></div><div><dt>Shipping</dt><dd>Free (US)</dd></div><div><dt>Taxes</dt><dd>At checkout</dd></div></dl>
    <button class="rd-btn rd-btn--primary rd-btn--full" type="button" data-rd-checkout>Checkout</button>
    <p class="rd-summary__msg" data-rd-cartmsg role="status" aria-live="polite"></p>
    <p class="rd-summary__note">{ICON["lock"]} Payments are processed securely by Stripe.</p>
    <a class="rd-textlink" href="{V}shop.html">Continue shopping</a>
  </aside>
</section>'''
    return page("Your cart · TRESORA", body, "cart")

def account_page():
    body = f'''
<section class="rd-section rd-account-page" data-rd-accountpage data-mode="signin">
  <div class="rd-account__card">
    <p class="rd-eyebrow">Your TRESORA account</p>
    <h1 data-rd-modal-title>Welcome back</h1>
    <div class="rd-modal__tabs" role="tablist"><button type="button" role="tab" data-rd-tab="signin" aria-selected="true">Sign in</button><button type="button" role="tab" data-rd-tab="signup" aria-selected="false">Create account</button></div>
    <form class="rd-auth" data-rd-auth novalidate>
      <label data-only="signup">Name<input name="name" autocomplete="name"></label>
      <label>Email<input name="email" type="email" autocomplete="email" required></label>
      <label>Password<span class="rd-pass"><input name="password" type="password" autocomplete="current-password" minlength="8" required><button type="button" class="rd-linkbtn" data-rd-showpass>Show</button></span></label>
      <label class="rd-check" data-only="signup"><input type="checkbox" name="news"> Email me new collections</label>
      <button class="rd-btn rd-btn--primary rd-btn--full" type="submit" data-rd-submit>Sign in</button>
      <button type="button" class="rd-linkbtn rd-forgot" data-only="signin" data-rd-forgot>Forgot password?</button>
      <p class="rd-auth__msg" data-rd-msg role="status" aria-live="polite"></p>
      <p class="rd-auth__note">Preview: accounts are not live yet. Nothing you type here is sent or stored.</p>
    </form>
  </div>
  <aside class="rd-account__perks"><h2>With an account</h2><ul><li>Track orders and delivery</li><li>Save addresses for faster checkout</li><li>Early access to new collections</li></ul><a class="rd-textlink" href="{V}shop.html">Continue as guest</a></aside>
</section>'''
    return page("Account · TRESORA", body, "account", active="account")

SHOT = '<p class="rd-viewall"><a class="rd-btn rd-btn--secondary" href="{V}shop.html">View the full collection</a></p>'
FACTS = '<ul class="rd-facts"><li>Complimentary US shipping</li><li>Secure checkout via Stripe</li><li><a href="#reviews">5.00 · 5 reviews</a></li></ul>'
def home():
    VP, VP45, FAN, BAG, AMALFI = (SH + "img/hero-vermeer-print.jpg", SH + "img/hero-vermeer-print-45.jpg", SH + "img/hero-barcelona-fan.jpg", SH + "img/hero-paris-bag.jpg", SH + "img/hero-amalfi.jpg")
    VG, KL = SH + "img/cat-art-vangogh.jpg", SH + "img/cat-art-klimt.jpg"
    va = SHOT.replace("{V}", V)
    def plink(h, label): return f'<a href="{purl(h)}">{E(label)}</a>'
    if N == 1: return f'''
<section class="rd-hero">
  <div class="rd-hero__text">
    <p class="rd-eyebrow">Art-inspired &amp; city-inspired gifts</p>
    <h1>Give the moment.<em>Keep the feeling.</em></h1>
    <p class="rd-lead">A rose tea cup after Klimt, a framed Vermeer, a Gaudí mosaic fan, a Parisian pearl bag. Curated objects you keep, not just open.</p>
    <div class="rd-cta"><a class="rd-btn rd-btn--primary" href="{V}shop.html">Shop the collection</a><a class="rd-textlink" href="#categories">Explore art &amp; cities</a></div>
    {FACTS}
  </div>
  <div class="rd-hero__mosaic">
    <a class="rd-tile rd-tile--tall" href="{purl("elegant-pearl-earring-table-gift-box")}"><img src="{VP45}" alt="Mini framed print of Vermeer’s Girl with a Pearl Earring on pearl tulle" width="1100" height="1375" fetchpriority="high"><span>Vermeer · mini framed print</span></a>
    <a class="rd-tile" href="{purl("barcelona-gift-box")}"><img src="{FAN}" alt="Park Güell mosaic hand fan and gold fan clutch" width="1200" height="900"><span>Barcelona · mosaic fan</span></a>
    <a class="rd-tile" href="{purl("paris-gift-box")}"><img src="{BAG}" alt="Pearl beaded evening bag" width="1200" height="900"><span>Paris · pearl evening bag</span></a>
  </div>
</section>
{trust("rd-trust--band")}
<section class="rd-section" id="categories"><header class="rd-head"><p class="rd-eyebrow">Collections</p><h2>Find your TRESORA</h2></header>{cat_tiles(VG)}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head"><p class="rd-eyebrow">The boutique</p><h2>The collection</h2></header>{grid()}{va}</section>
<section class="rd-section rd-story"><div class="rd-story__intro"><p class="rd-eyebrow">Why TRESORA</p><h2>Gifts with a<br><em>story inside.</em></h2>
  <p class="rd-lead">Not another gift that gets forgotten. Every piece is chosen around a painting, a city or a moment.</p></div>{why()}</section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head"><p class="rd-eyebrow">Reviews</p><h2>Loved by the people who receive them</h2></header>{reviews()}</section>
<section class="rd-section rd-section--news">{newsletter()}</section>'''
    if N == 2: return f'''
<section class="rd-hero">
  <figure class="rd-hero__frame"><div class="rd-mat"><img src="{VP}" alt="Mini framed print of Vermeer’s Girl with a Pearl Earring on pearl tulle" width="1400" height="1400" fetchpriority="high"></div>
    <figcaption>Mini framed print of <em>Girl with a Pearl Earring</em> · {plink("elegant-pearl-earring-table-gift-box", "Elegant Pearl Earring Table")}</figcaption></figure>
  <div class="rd-hero__text">
    <p class="rd-eyebrow">Art &amp; Places</p>
    <h1>Gifts curated<em>like a gallery.</em></h1>
    <span class="rd-rule" aria-hidden="true"></span>
    <p class="rd-lead">Objects inspired by a painting or a city: Klimt’s rose tea cup, Vermeer’s pearl light, Sargent’s wineglasses, Gaudí’s mosaics.</p>
    <div class="rd-cta"><a class="rd-btn rd-btn--primary" href="{V}shop.html">Visit the collection</a><a class="rd-textlink" href="#reviews">Read the guest book</a></div>
    {FACTS}
  </div>
</section>
<section class="rd-section rd-section--trust">{trust()}</section>
<section class="rd-section" id="categories"><header class="rd-head"><p class="rd-eyebrow">The rooms</p><h2>Choose your wing</h2></header>{cat_tiles(KL)}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head"><p class="rd-eyebrow">Catalogue</p><h2>The collection</h2><p>Open any piece to see everything inside.</p></header>{grid("rd-grid--gallery")}{va}</section>
<section class="rd-section rd-why-wrap"><header class="rd-head"><p class="rd-eyebrow">Curator’s note</p><h2>Why TRESORA</h2></header>{why()}</section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head"><p class="rd-eyebrow">Guest book</p><h2>What our visitors say</h2></header>{reviews()}</section>
<section class="rd-section rd-section--news">{newsletter("Be first at the next opening.", "New collections and limited editions, a few times a year. Unsubscribe anytime.")}</section>'''
    return f'''
<section class="rd-hero">
  <div class="rd-hero__text">
    <p class="rd-eyebrow">Art &amp; City collections</p>
    <h1>Gifts inspired by art and the cities you love.</h1>
    <p class="rd-lead">Amalfi lemons and a Vespa charm, a Parisian pearl bag, a Klimt rose tea cup. Curated sets and handmade objects with free US shipping.</p>
    <div class="rd-cta"><a class="rd-btn rd-btn--primary" href="{V}shop.html">Shop all</a><a class="rd-textlink" href="{V}shop.html?cat=city">City collection from {from_price("city")}</a></div>
    {FACTS}
  </div>
  <a class="rd-hero__media" href="{purl("amalfi-gift-box")}"><img src="{AMALFI}" alt="Amalfi majolica compact mirror, lipstick in an ornate case and Riviera print scarf with lemons" width="1200" height="1200" fetchpriority="high"><span class="rd-hero__tag">From the Amalfi set · $49.00</span></a>
</section>
<section class="rd-section rd-section--trust">{trust()}</section>
<section class="rd-section" id="categories"><header class="rd-head rd-head--row"><h2>Shop by category</h2><a class="rd-textlink" href="{V}shop.html">View all</a></header>{cat_tiles(VG)}</section>
<section class="rd-section rd-section--shop" id="shop"><header class="rd-head rd-head--row"><h2>All products</h2><a class="rd-textlink" href="{V}shop.html">Filters &amp; sorting</a></header>{grid("rd-grid--dense")}</section>
<section class="rd-section rd-section--reviews" id="reviews"><header class="rd-head rd-head--row"><h2>Customer reviews</h2></header>{reviews()}</section>
<section class="rd-section rd-why-wrap"><header class="rd-head rd-head--row"><h2>Why shop with TRESORA</h2></header>{why()}</section>
<section class="rd-section rd-section--news">{newsletter("Get the first look at new collections", "One short email when something new arrives. Unsubscribe anytime.")}</section>'''

NAMES = {1: "Midnight", 2: "Gallery", 3: "Modern"}
count = 0
for N in (1, 2, 3):
    V = f"{R}redesign/v{N}/"
    d = f"redesign/v{N}"; os.makedirs(f"{d}/products", exist_ok=True)
    def w(path, txt):
        global count; open(f"{d}/{path}", "w", encoding="utf-8").write(txt); count += 1
    w("index.html", page(f"TRESORA · Concept {N} · {NAMES[N]}", home(), "home"))
    w("shop.html", shop_page()); w("cart.html", cart_page()); w("account.html", account_page())
    for h in ORDER: w(f"products/{h}.html", product_page(h))
print(f"built {count} pages in redesign/v1..v3")
