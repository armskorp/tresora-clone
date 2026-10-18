"""Build a static, offline copy of the tresora.store homepage from the JS-rendered DOM
captured in orig/rendered.html. Downloads CSS, fonts and images into assets/."""
import re, os, time, json, hashlib, subprocess, urllib.parse as up, html
from bs4 import BeautifulSoup, Comment

ROOT = "/workspace/tresora-clone"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
os.chdir(ROOT)
for d in ["assets/css", "assets/fonts", "assets/images", "products"]:
    os.makedirs(d, exist_ok=True)

widths = json.load(open("orig/img_widths.json"))["widths"]
products = {p["handle"]: p for p in json.load(open("orig/products.json"))["products"]}
cache = {}

def absu(u, base="https://tresora.store/"):
    u = html.unescape(u.strip())
    if u.startswith("//"): u = "https:" + u
    return up.urljoin(base, u)

def fetch(url, folder, name=None):
    """download url into assets/<folder>/ and return path relative to site root"""
    if url in cache: return cache[url]
    p = up.urlparse(url)
    base = os.path.basename(p.path) or "file"
    stem, ext = os.path.splitext(base)
    q = up.parse_qs(p.query)
    tag = ""
    if "width" in q: tag += "-w" + q["width"][0]
    if "height" in q: tag += "-h" + q["height"][0]
    fname = name or (re.sub(r"[^A-Za-z0-9._-]", "_", stem)[:60] + tag + "-" + hashlib.md5(url.encode()).hexdigest()[:6] + ext)
    out = f"assets/{folder}/{fname}"
    if not os.path.exists(out) or os.path.getsize(out) == 0:
        for attempt in range(4):
            r = subprocess.run(["curl", "-sfL", "-A", UA, "-o", out, url])
            if r.returncode == 0 and os.path.getsize(out) > 0: break
            time.sleep(2 + attempt * 3)
        else:
            print("FAIL", url); cache[url] = None
            if os.path.exists(out): os.remove(out)
            return None
    cache[url] = out
    return out

def with_width(url, w):
    p = up.urlparse(url); q = up.parse_qs(p.query)
    q = {k: v[0] for k, v in q.items()}
    q.pop("height", None) if "width" in q or w else None
    q["width"] = str(w)
    return up.urlunparse(p._replace(query=up.urlencode(q)))

STD = [240, 360, 480, 640, 800, 1000, 1200, 1600, 2000]
def local_img(src):
    url = absu(src)
    if "cdn/shop/" in url and "width=" in url or ("cdn/shop/" in url and "height=" not in url):
        need = widths.get(src, 600) * 2
        w = next((x for x in STD if x >= need), STD[-1])
        url = with_width(url, w)
    return fetch(url, "images")

def css_urls(css, base, rel_prefix):
    """localise url(...) inside css text; rel_prefix = path from css location to site root"""
    def rep(m):
        q, u = m.group(1), m.group(2)
        if u.startswith("data:") or u.startswith("#"): return m.group(0)
        if "%D0%92%D0%90%D0%A8" in u or "ВАШ" in u: return "url()"  # broken placeholder on live site
        full = absu(u, base)
        folder = "fonts" if re.search(r"\.(woff2?|ttf|otf|eot)(\?|$)", full) else "images"
        loc = fetch(full, folder)
        return f"url({q}{rel_prefix}{loc}{q})" if loc else m.group(0)
    return re.sub(r"url\((['\"]?)([^)'\"]+)\1\)", rep, css)

src = open("orig/rendered.html", encoding="utf-8").read()
soup = BeautifulSoup(src, "html.parser")

# ---------- strip runtime / third-party noise ----------
for c in soup.find_all(string=lambda t: isinstance(t, Comment)): c.extract()
for t in soup.find_all(["script", "noscript", "iframe", "template"]): t.decompose()
# body-level app embeds (Judge.me loader, Shopify Forms) - the in-page review widget stays
for e in soup.body.find_all("div", class_="shopify-app-block", recursive=False): e.decompose()
# re-insert the declarative shadow root of <overflow-list> (header menu); page.content() drops it
raw = open("orig/server.html", encoding="utf-8").read()
i = raw.find('<template shadowrootmode="open">'); j = raw.find("</template>", i) + len("</template>")
tpl = raw[i:j]
ol_css = fetch(absu(re.search(r'href="([^"]*overflow-list\.css[^"]*)"', tpl).group(1)), "css", "overflow-list.css")
tpl = re.sub(r'href="[^"]*overflow-list\.css[^"]*"', 'href="' + ol_css + '"', tpl)
for ol in soup.find_all("overflow-list"):
    ol.insert(0, BeautifulSoup(tpl, "html.parser"))
for sel in ["#chat-drawer", "#shopify-section-cart-drawer-section", "#search-modal", "#quick-add-dialog",
            "#web-pixels-manager-sandbox-container", "shop-cart-sync", "shopify-forms-embed", "shopify-chat",
            "#jdgm-carousel-lightbox-root", ".jdgm-random-link", "link.jdgm-prefetch",
            "#shopify-section-template--20011747344497__hero_jVaWmY .hero__media-wrapper ~ noscript"]:
    for e in soup.select(sel): e.decompose()
for l in soup.find_all("link"):
    rel = " ".join(l.get("rel", []))
    if rel not in ("stylesheet", "icon"): l.decompose()
for m in soup.find_all("meta"):
    if m.get("name") not in ("viewport", "description") and not m.get("charset") and m.get("property") not in ("og:title", "og:description"):
        m.decompose()

# ---------- stylesheets ----------
seen = set()
for l in soup.find_all("link"):
    if l["href"].startswith("assets/"): continue  # already localised (overflow-list shadow root)
    href = absu(l["href"])
    if "icon" in l.get("rel", []):
        loc = fetch(href, "images", "favicon.png"); l["href"] = loc; continue
    if "accelerated-checkout" in href or href in seen:
        l.decompose(); continue
    seen.add(href)
    name = os.path.basename(up.urlparse(href).path)
    if "judgeme" in href: name = "judgeme-" + name
    out = f"assets/css/{name}"
    for attempt in range(4):
        css = subprocess.run(["curl", "-sfL", "-A", UA, href], capture_output=True, text=True).stdout
        if css.strip(): break
        time.sleep(2 + attempt * 3)
    assert css.strip(), "empty stylesheet " + href
    css = css_urls(css, href, "../../")
    open(out, "w").write(css)
    l.attrs = {"rel": "stylesheet", "href": out}
for st in soup.find_all("style"):
    st.string = css_urls(st.string or "", "https://tresora.store/", "")

# ---------- inline style url() ----------
for e in soup.find_all(style=True):
    e["style"] = css_urls(e["style"], "https://tresora.store/", "")

# ---------- images ----------
for img in soup.find_all("img"):
    s = img.get("src")
    if not s: continue
    loc = local_img(s)
    if loc: img["src"] = loc
    for a in ("srcset", "sizes", "data-srcset"): img.attrs.pop(a, None)
    img["loading"] = img.get("loading", "lazy")
for so in soup.find_all("source"):
    ss = so.get("srcset", "")
    first = ss.split(",")[0].strip().split(" ")[0] if ss else None
    if first:
        loc = local_img(first); so["srcset"] = loc
# svg <image href>
for im in soup.find_all("image"):
    h = im.get("href") or im.get("xlink:href")
    if h and not h.startswith("data:"):
        loc = fetch(absu(h), "images"); im["href"] = loc

# ---------- links & forms ----------
def product_handle(href):
    m = re.search(r"/products/([^/?#]+)", href)
    return m.group(1) if m else None
for a in soup.find_all("a", href=True):
    h = a["href"]
    ph = product_handle(h)
    if ph and ph in products: a["href"] = f"products/{ph}.html"
    elif h.startswith("#"): pass
    else: a["href"] = "#"
    a.attrs.pop("target", None) if a["href"] == "#" else None
for f in soup.find_all("form"):
    f["action"] = "#"; f["onsubmit"] = "return false"
    f.attrs.pop("data-shopify", None)
for e in soup.find_all(attrs={"data-shopify-editor-section": True}): del e["data-shopify-editor-section"]

# ---------- drop leftover attributes that point at the live CDN ----------
for e in soup.find_all(True):
    for k, v in list(e.attrs.items()):
        if isinstance(v, str) and re.search(r"(tresora\.store|cdn\.shopify|myshopify)", v) and k not in ("href", "src"):
            del e.attrs[k]

# ---------- clone overrides + minimal JS ----------
head = soup.head
head.append(soup.new_tag("link", rel="stylesheet", href="assets/css/clone.css"))
js = soup.new_tag("script", src="assets/js/clone.js", defer=True)
soup.body.append(js)
soup.html["data-static-clone"] = "true"

open("index.html", "w", encoding="utf-8").write("<!doctype html>\n" + str(soup).replace("<!DOCTYPE html>", "", 1))

# ---------- product placeholder pages (real data from /products.json) ----------
for h, p in products.items():
    img = p["images"][0]["src"] if p["images"] else None
    loc = fetch(with_width(img, 800), "images") if img else None
    price = p["variants"][0]["price"] if p["variants"] else ""
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p['title'])} – TRESORA</title><link rel="icon" href="../assets/images/favicon.png"><link rel="stylesheet" href="../assets/css/product-placeholder.css"></head>
<body><main class="pp"><a class="pp__back" href="../index.html">← TRESORA</a>
{f'<img src="../{loc}" alt="{html.escape(p["title"])}">' if loc else ''}
<h1>{html.escape(p['title'])}</h1><p class="pp__price">${price} USD</p>
<div class="pp__body">{p.get('body_html') or ''}</div>
<p class="pp__note">Static placeholder page of the local homepage copy.</p></main></body></html>"""
    open(f"products/{h}.html", "w").write(page)
print("done; files:", len(cache))
