"""Homepage hero slideshow (index.html): slide order, images and captions. Idempotent; run after any page rebuild
(tools/add_ga.py calls it). Slides are full-bleed (object-fit: cover, full viewport height, behind the header) with a focal
point per slide: --pos-d on landscape screens, --pos-m on portrait phones (.rd-slide--cover in redesign/v4/style.css)."""
import html, json, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
E = html.escape
P = "/redesign/shared/products/"
# (name, product handle, image, alt, kicker); focal points are in POS below
SLIDES = [
  ("Amalfi", "amalfi-gift-box", "amalfi-gift-box-0.jpg",
   "The open Amalfi gift box: lemon-print scarf, straw mini bag, majolica compact mirror, Vespa charm with pearls, lipstick case and charm necklace", "Inspired by City"),
  ("Gothic Romance", "gothic-romance-decorative-glass-bottle", "gothic-romance-decorative-glass-bottle-1.jpg",
   "Gothic Romance hand-decorated glass bottle with a red rose, on a dark stand before red velvet drapes", "Atelier Home"),
  ("Caravaggio", "caravaggio-bacchus-wine-gift-box", "caravaggio-bacchus-wine-gift-box-3.jpg",
   "The open Caravaggio Bacchus wine gift box: red cable-knit throw, two wine glasses, wine opener set, candle, reed diffuser and framed Bacchus print", "Inspired by Art"),
  ("Gothic Portraits", "gothic-portraits-decorative-glass-vase", "gothic-portraits-decorative-glass-vase-0.jpg",
   "Gothic Portraits handcrafted decorative glass vase with a painted portrait and red roses, on an antique mantel", "Atelier Home"),
  ("Paris", "paris-gift-box", "paris-gift-box-0.jpg",
   "The open Paris gift box: pearl beaded evening bag, black lace bow, pearl bow earrings, charm and card", "Inspired by City"),
  ("Crow & Roses", "crow-roses-decorative-bottle", "crow-roses-decorative-bottle-0.jpg",
   "Crow & Roses handcrafted decorative glass bottle with red and black roses, on an antique mantel", "Atelier Home"),
  ("Sargent", "sargent-the-wineglasses-wine-gift-box", "sargent-the-wineglasses-wine-gift-box-0.jpg",
   "The open John Sargent The Wineglasses gift box: two stemless wine glasses, cheese board and knives, pearl tulle, candle and framed print", "Inspired by Art"),
]
POS = {  # image -> (desktop object-position, mobile object-position)
  "amalfi-gift-box-0.jpg": ("50% 52%", "52% 50%"),
  "gothic-romance-decorative-glass-bottle-1.jpg": ("50% 62%", "50% 55%"),
  "caravaggio-bacchus-wine-gift-box-3.jpg": ("50% 52%", "48% 50%"),
  "gothic-portraits-decorative-glass-vase-0.jpg": ("50% 74%", "55% 50%"),
  "paris-gift-box-0.jpg": ("50% 50%", "40% 50%"),
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
    <img class="rd-slide__img" src="{src}" alt="{E(alt)}" style="--pos-d:{POS[img][0]};--pos-m:{POS[img][1]}" {"fetchpriority=\"high\"" if i == 0 else 'loading="eager"'} decoding="async">
    <figcaption class="rd-slide__text"><span class="rd-slide__kicker">{kicker} · {i+1:02d}</span><span class="rd-slide__city{long}">{E(name)}</span>
      <a class="rd-slide__link" href="/products/{h}.html"{tab}>{verb} {E(name)}</a><span class="rd-slide__price">{E(p["title"])} · {price}</span></figcaption></figure>''')
    dots.append(f'<button type="button" class="rd-dot" data-rd-dot="{i}" aria-label="Show {E(name)}"{" aria-current=\"true\"" if i == 0 else ""}><span></span></button>')
f = "index.html"; s = o = open(f, encoding="utf-8").read()
s, a = re.subn(r'(<div class="rd-slides__track" aria-live="off">).*?(</div>\n  <div class="rd-slides__nav")', lambda m: m.group(1) + "".join(figs) + m.group(2), s, count=1, flags=re.S)
s, b = re.subn(r'(<div class="rd-slides__nav" role="group" aria-label="Choose a slide">).*?(</div>)', lambda m: m.group(1) + "".join(dots) + m.group(2), s, count=1, flags=re.S)
assert a == 1 and b == 1, "hero markup not found in index.html"
s = s.replace('aria-label="Cities and Atelier Home"', 'aria-label="Featured gifts"')
# preload the first slide image for a fast first paint
s = re.sub(r'<link rel="preload" as="image" href="[^"]*" data-rd-hero>\n?', "", s)
s = s.replace("</head>", f'<link rel="preload" as="image" href="{P + SLIDES[0][2]}" data-rd-hero>\n</head>', 1)
s = re.sub(r'redesign/v4/style\.css\?v=[0-9a-z]+', 'redesign/v4/style.css?v=20261109i', s)  # hero CSS changed
if s != o: open(f, "w", encoding="utf-8").write(s)
print(f"hero: {n} slides -> " + ", ".join(x[0] for x in SLIDES))
