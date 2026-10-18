"""Product-first imagery for the redesign concepts: lead images that show the items (not the packaging),
plus hero/tile crops. Sources: orig/pimg (store gallery originals) and orig/hires. usage: python3 tools/prep_redesign_images.py"""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
P, H, OUT, IMG = "orig/pimg/", "orig/hires/", "redesign/shared/products/", "redesign/shared/img/"
def crop(im, cx=.5, cy=.5, s=1.0, ar=4/3):
    W, Hh = im.size; w = s * W; h = w / ar
    if h > Hh: h = Hh; w = h * ar
    x = min(max(0, cx * W - w / 2), W - w); y = min(max(0, cy * Hh - h / 2), Hh - h)
    return im.crop((int(x), int(y), int(x + w), int(y + h)))
def save(im, path, maxw, q=84):
    im = im.convert("RGB")
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), Image.LANCZOS)
    im.save(path, quality=q, optimize=True, progressive=True)
def src(name): return Image.open(P + name if os.path.exists(P + name) else H + name)
# lead image per product (and per color variant): the items themselves, tight crops where the store only shot them in the box
LEADS = {
  "amalfi-gift-box": ("amalfi-gift-box-2", .5, .5, 1), "barcelona-gift-box": ("barcelona-gift-box-2", .5, .5, 1),
  "new-york-gift-box": ("new-york-gift-box-1", .5, .5, 1), "paris-gift-box": ("paris-gift-box-2", .5, .5, 1),
  "klimt-the-kiss-gift-box": ("klimt-the-kiss-gift-box-1", .5, .5, 1), "elegant-pearl-earring-table-gift-box": ("elegant-pearl-earring-table-gift-box-2", .5, .5, .55),
  "van-gogh-almond-blossom-gift-box": ("van-gogh-almond-blossom-gift-box-5", .5, .5, 1), "sargent-the-wineglasses-wine-gift-box": ("sargent-the-wineglasses-wine-gift-box-0", .6, .62, .5),
  "caravaggio-bacchus-wine-gift-box-green": ("caravaggio-bacchus-wine-gift-box-0", .5, .55, .5), "caravaggio-bacchus-wine-gift-box-red": ("caravaggio-bacchus-wine-gift-box-3", .5, .55, .5),
  "vermeer-girl-with-a-pearl-earring-gift-box-light-blue": ("vermeer-girl-with-a-pearl-earring-gift-box-2", .47, .52, .4),
  "vermeer-girl-with-a-pearl-earring-gift-box-white": ("vermeer-girl-with-a-pearl-earring-gift-box-1", .45, .52, .4),
  "gothic-romance-decorative-glass-bottle": ("gothic-romance-decorative-glass-bottle-0", .5, .48, 1), "rococo-reverie-decorative-glass-bottle": ("rococo-reverie-decorative-glass-bottle-0", .5, .5, 1),
}
for key, (name, cx, cy, s) in LEADS.items():
    im = crop(src(name).convert("RGB"), cx, cy, s)
    save(im, f"{OUT}{key}-lead.jpg", 1200); t = im.copy(); t.thumbnail((240, 240)); save(t, f"{OUT}{key}-lead-t.jpg", 240, 80)
# heroes + tiles (no packaging in frame)
art = src("elegant-pearl-earring-table-gift-box-2").convert("RGB")
save(crop(art, .5, .5, .42, 1), IMG + "hero-vermeer-print.jpg", 1400)          # mini framed Vermeer print on pearl tulle
save(crop(art, .5, .5, .42, 4/5), IMG + "hero-vermeer-print-45.jpg", 1100)
save(crop(src("barcelona-gift-box-2").convert("RGB"), .5, .5, 1, 4/3), IMG + "hero-barcelona-fan.jpg", 1200)
save(crop(src("paris-gift-box-2").convert("RGB"), .5, .5, 1, 4/3), IMG + "hero-paris-bag.jpg", 1200)
save(crop(src("amalfi-gift-box-6").convert("RGB"), .5, .5, 1, 1), IMG + "hero-amalfi.jpg", 1200)
save(crop(src("van-gogh-almond-blossom-gift-box-5").convert("RGB"), .5, .5, 1, 4/5), IMG + "cat-art-vangogh.jpg", 1000)
save(crop(src("klimt-the-kiss-gift-box-1").convert("RGB"), .42, .5, 1, 4/5), IMG + "cat-art-klimt.jpg", 1000)
print("ok")
# v4 city slideshow: full-bleed styled photos of each city set's items (native resolution, no packaging in frame)
SLIDES = {"paris": "paris-gift-box-2", "barcelona": "barcelona-gift-box-2", "new-york": "new-york-gift-box-1", "amalfi": "amalfi-gift-box-1",
          "rococo": "rococo-reverie-decorative-glass-bottle-1", "gothic": "gothic-romance-decorative-glass-bottle-0"}
for city, name in SLIDES.items():
    im = src(name).convert("RGB"); save(im, f"{IMG}slide-{city}.jpg", 2000, 86)
print("slides ok")
