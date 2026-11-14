"""Homepage hero slideshow (index.html): slide order, images and captions. Idempotent; run after any page rebuild
(tools/add_ga.py calls it). Slides are full-bleed (object-fit: cover, full viewport height, behind the header) with a focal
point per slide: --pos-d on landscape screens, --pos-m on portrait phones (.rd-slide--cover in redesign/v4/style.css)."""
import html, json, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
E = html.escape
P = "/redesign/shared/products/"
# (name, product handle, image, alt, kicker); focal points are in POS below
SLIDES = [
  ("Amalfi", "amalfi-gift-box", "amalfi-hero-wide-v2.jpg",
   "The open Amalfi gift box: lemon-print scarf, straw mini bag, majolica compact mirror, Vespa charm with pearls, lipstick case and charm necklace", "Inspired by City"),
  ("Caravaggio", "caravaggio-bacchus-wine-gift-box", "caravaggio-green-hero-wide-v2.jpg",
   "The open Caravaggio Bacchus wine gift box: forest green cable-knit throw with satin ribbon, two wine glasses, wine opener set, reed diffuser and framed Bacchus print", "Inspired by Art"),
  ("Gothic Romance", "gothic-romance-decorative-glass-bottle", "gothic-romance-hero-wide-v2.jpg",
   "Gothic Romance hand-decorated glass bottle with a black rose, on a carved wooden table between candelabra", "Atelier Home"),
  ("Paris", "paris-gift-box", "paris-hero-wide.jpg",
   "The open Paris gift box: pearl beaded evening bag, black and white silk scarf, black lace bow, pearl bow earrings, doll charm and card", "Inspired by City"),
  ("Gothic Portraits", "gothic-portraits-decorative-glass-vase", "gothic-trio-hero-wide.jpg",
   "Three hand-decorated gothic pieces: a portrait jar, a small crystal-stopper bottle and a round bottle with a skull and red roses, by candlelight in a gothic room", "Atelier Home"),
  ("New York", "new-york-gift-box", "new-york-hero-wide.jpg",
   "The open New York gift box: silver cage handbag, 1920s newspaper print silk scarf, compact mirror, rhinestone chain, art deco drop earrings and airplane charm card", "Inspired by City"),
  ("Caravaggio", "caravaggio-bacchus-wine-gift-box", "caravaggio-red-hero-wide.jpg",
   "The open Caravaggio Bacchus wine gift box: red cable-knit throw with satin ribbon, two wine glasses with red bows, wine opener set, reed diffuser and gold-framed Bacchus print", "Inspired by Art"),
  ("Van Gogh", "van-gogh-almond-blossom-gift-box", "van-gogh-hero-wide-v3.jpg",
   "The open Van Gogh Almond Blossom gift box: light blue pearl tulle, blue glass reed diffuser, gold-framed mini print, chocolate bar, navy candle in a brass holder and a glass butterfly mug with gold spoon", "Inspired by Art"),
  ("Crow & Roses", "crow-roses-decorative-bottle", "crow-roses-decorative-bottle-0.jpg",
   "Crow & Roses handcrafted decorative glass bottle with red and black roses, on an antique mantel", "Atelier Home"),
  ("Sargent", "sargent-the-wineglasses-wine-gift-box", "sargent-the-wineglasses-wine-gift-box-0.jpg",
   "The open John Sargent The Wineglasses gift box: two stemless wine glasses, cheese board and knives, pearl tulle, candle and framed print", "Inspired by Art"),
]
MOBILE = {  # image -> separate portrait image for phones
  "amalfi-hero-wide-v2.jpg": "amalfi-hero-mobile.jpg",
  "caravaggio-green-hero-wide-v2.jpg": "caravaggio-green-hero-mobile.jpg",
  "gothic-romance-hero-wide-v2.jpg": "gothic-romance-hero-mobile-v2.jpg",
  "paris-hero-wide.jpg": "paris-hero-mobile.jpg",
  "gothic-trio-hero-wide.jpg": "gothic-trio-hero-mobile.jpg",
  "new-york-hero-wide.jpg": "new-york-hero-mobile.jpg",
  "caravaggio-red-hero-wide.jpg": "caravaggio-red-hero-mobile.jpg",
  "van-gogh-hero-wide-v3.jpg": "van-gogh-hero-mobile.jpg",
}
POS = {  # image -> (desktop object-position, mobile object-position)
  "amalfi-hero-wide-v2.jpg": ("50% 50%", "50% 50%"),
  "gothic-romance-hero-wide-v2.jpg": ("50% 50%", "50% 50%"),
  "caravaggio-green-hero-wide-v2.jpg": ("50% 50%", "50% 50%"),
  "gothic-portraits-decorative-glass-vase-0.jpg": ("50% 74%", "55% 50%"),
  "paris-hero-wide.jpg": ("50% 50%", "50% 50%"),
  "gothic-trio-hero-wide.jpg": ("50% 50%", "50% 50%"),
  "new-york-hero-wide.jpg": ("50% 50%", "50% 50%"),
  "caravaggio-red-hero-wide.jpg": ("50% 50%", "50% 50%"),
  "van-gogh-hero-wide-v3.jpg": ("50% 50%", "50% 50%"),
  "crow-roses-decorative-bottle-0.jpg": ("50% 76%", "52% 50%"),
  "sargent-the-wineglasses-wine-gift-box-0.jpg": ("50% 62%", "52% 50%"),
}
s = open("assets/js/catalog.js").read()
CAT = json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])
BY = {p["handle"]: p for p in CAT["products"].values()}
def money(c): return f"${c/100:.2f}"
n = len(SLIDES); figs = []; dots = []
for i, (name, h, img, alt, kicker) in enumerate(SLIDES):
    p = BY[h]; vs = [CAT["variants"][str(v)] for v in p["variants"]]
    avail = [v for v in vs if v["available"]]; tab = "" if i == 0 else ' tabindex="-1"'
    price = (("From " if len({v["price"] for v in avail}) > 1 else "") + money(min(v["price"] for v in avail))) if avail else "Sold out"
    verb = "Shop" if avail else "View"; long = " rd-slide__city--long" if len(name) > 10 else ""
    src = P + img
    figs.append(f'''<figure class="rd-slide{" is-active" if i == 0 else ""} rd-slide--cover" data-rd-slide aria-roledescription="slide" aria-label="{i+1} of {n}: {E(name)}"{"" if i == 0 else ' aria-hidden="true"'}>
    {('<picture style="display:contents"><source media="(max-aspect-ratio:1/1)" srcset="' + P + MOBILE[img] + '">') if img in MOBILE else ''}<img class="rd-slide__img" src="{src}" alt="{E(alt)}" style="--pos-d:{POS[img][0]};--pos-m:{POS[img][1]}" {"fetchpriority=\"high\" decoding=\"sync\"" if i == 0 else 'loading="lazy" fetchpriority="low" decoding="async"'}>{'</picture>' if img in MOBILE else ''}
    <figcaption class="rd-slide__text"><span class="rd-slide__kicker">{kicker} · {i+1:02d}</span><span class="rd-slide__city{long}">{E(name)}</span>
      <a class="rd-slide__link" href="/products/{h}.html"{tab}>{verb} {E(name)}</a><span class="rd-slide__price">{E(p["title"])} · {price}</span></figcaption></figure>''')
    dots.append(f'<button type="button" class="rd-dot" data-rd-dot="{i}" aria-label="Show {E(name)}"{" aria-current=\"true\"" if i == 0 else ""}><span></span></button>')
f = "index.html"; s = o = open(f, encoding="utf-8").read()
s, a = re.subn(r'(<div class="rd-slides__track" aria-live="off">).*?(</div>\n  <div class="rd-slides__nav")', lambda m: m.group(1) + "".join(figs) + m.group(2), s, count=1, flags=re.S)
s, b = re.subn(r'(<div class="rd-slides__nav" role="group" aria-label="Choose a slide">).*?(</div>)', lambda m: m.group(1) + "".join(dots) + m.group(2), s, count=1, flags=re.S)
assert a == 1 and b == 1, "hero markup not found in index.html"
s = s.replace('aria-label="Cities and Atelier Home"', 'aria-label="Featured gifts"')
# preload the first slide image for a fast first paint.
# Use width media queries (Safari often ignores aspect-ratio on rel=preload).
# fetchpriority=high so the first painting is requested before later slides.
s = re.sub(r'<link rel="preload" as="image"[^>]*>\n?', "", s)
mobile0 = MOBILE.get(SLIDES[0][2])
pre = (
    f'<link rel="preload" as="image" href="{P + SLIDES[0][2]}" media="(min-width: 750px)" fetchpriority="high" data-rd-hero>\n'
    + (f'<link rel="preload" as="image" href="{P + mobile0}" media="(max-width: 749px)" fetchpriority="high">\n' if mobile0 else "")
)
s = s.replace("</head>", pre + "</head>", 1)

# Sharper inline LQIP so the first painting is recognizable on first paint
# (the previous 48px placeholder read as a muddy olive-brown field).
# Keep #rd-hero-lqip and the navy fallback behind the image (do not change slide bg).
try:
    import base64, io
    from PIL import Image
    def _lqip(path, box, quality):
        im = Image.open(path).convert("RGB")
        im.thumbnail(box, Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=quality, optimize=True, subsampling=0)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    wide_src = "redesign/shared/products/" + SLIDES[0][2]
    lqip_d = _lqip(wide_src, (240, 135), 42)
    lqip_m = _lqip("redesign/shared/products/" + mobile0, (96, 208), 42) if mobile0 else lqip_d
    lqip_css = (
        '.rd-slides{background:#0d1726 url(' + lqip_d + ') 50% 50%/cover no-repeat}'
        '@media (max-aspect-ratio:1/1){.rd-slides{background-image:url(' + lqip_m + ')}}'
    )
    if 'id="rd-hero-lqip"' in s:
        s, n_lqip = re.subn(
            r'<style id="rd-hero-lqip">.*?</style>',
            '<style id="rd-hero-lqip">' + lqip_css + '</style>',
            s, count=1, flags=re.S,
        )
        assert n_lqip == 1, "rd-hero-lqip replace failed"
    else:
        s = s.replace("</head>", '<style id="rd-hero-lqip">' + lqip_css + '</style>\n</head>', 1)
except Exception as e:
    print("lqip: left existing placeholder (" + str(e) + ")")

if s != o: open(f, "w", encoding="utf-8").write(s)
print(f"hero: {n} slides -> " + ", ".join(x[0] for x in SLIDES))
