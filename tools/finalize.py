"""Post-build hardening (run last; build_shop.py calls it). Idempotent.
 - product-card photos: first slide = plain eager <img> with real pixel dimensions, high priority for
   the first cards of each row; no decoding/lazy tricks on the photo that must be visible
 - every local <img> gets its real width/height (the snapshot kept Shopify's 3840px originals' sizes)
 - cache-busting ?v=<content hash> on local CSS/JS in every page (iOS Safari caches hard)"""
import hashlib, os, re, glob
from bs4 import BeautifulSoup
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
dims = {}
def size(path):
    if path not in dims:
        try:
            with Image.open(path) as im: dims[path] = im.size
        except Exception: dims[path] = None
    return dims[path]

idx = open("index.html", encoding="utf-8").read()
soup = BeautifulSoup(idx, "html.parser")
fixed = 0
for img in soup.find_all("img"):
    src = (img.get("src") or "").split("?")[0]
    if src.startswith("assets/") and size(src):
        w, h = size(src); img["width"], img["height"] = str(w), str(h)
notes = []
for track in soup.select("slideshow-slides"):
    if track.find_parent("product-card") is None: continue      # card galleries only
    slides = track.find_all("slideshow-slide", recursive=False)
    if not slides: continue
    vis = [s for s in slides if s.get("aria-hidden") == "false"]
    if vis and vis[0] is not slides[0]:                          # make the visible photo the first slide
        vis[0].extract(); track.insert(0, vis[0]); slides = track.find_all("slideshow-slide", recursive=False)
        notes.append("reordered")
    first = slides[0]
    first["aria-hidden"] = "false"
    if first.has_attr("hidden"): del first["hidden"]
    img = first.find("img")
    if img:
        img["loading"] = "eager"
        for a in ("decoding", "srcset", "sizes"):
            if img.has_attr(a): del img[a]
        fixed += 1
# first two cards of each row are above the fold on phones: fetch them first
for row in soup.select(".resource-list__carousel slideshow-slides"):
    cards = [s for s in row.find_all("slideshow-slide", recursive=False) if s.find("product-card")]
    for i, s in enumerate(cards):
        im = s.find("product-card").select_one("slideshow-slide img")
        if im: im["fetchpriority"] = "high" if i < 2 else "auto"
out = str(soup)
if "assets/js/payment-links.js" not in out:
    out = re.sub(r'(<script src="assets/js/catalog\.js[^"]*"></script>)', r'\1\n<script src="assets/js/payment-links.js"></script>', out, count=1)
open("index.html", "w", encoding="utf-8").write(out)

def hsh(p):
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:10]
def bust(html, base):
    def rep(m):
        attr, q, url = m.group(1), m.group(2), m.group(3)
        clean = url.split("?")[0]
        local = os.path.normpath(os.path.join(base, clean))
        if not os.path.isfile(local): return m.group(0)
        return f'{attr}={q}{clean}?v={hsh(local)}{q}'
    return re.sub(r'(href|src)=(["\'])((?:\.\./)?assets/(?:css|js)/[^"\'?]+\.(?:css|js)(?:\?[^"\']*)?)\2', rep, html)
pages = ["index.html", "success.html", "cancel.html"] + sorted(glob.glob("products/*.html"))
for p in pages:
    s = open(p, encoding="utf-8").read()
    t = bust(s, os.path.dirname(p) or ".")
    if t != s: open(p, "w", encoding="utf-8").write(t)
print(f"finalize: {fixed} card photos hardened, {len(dims)} images sized, {len(pages)} pages cache-busted", notes[:3])
