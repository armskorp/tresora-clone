"""Build product galleries from orig/gallery/<handle>/ masters.

The vintage ornament card shipped sideways because the published JPEGs were
already landscape pixels with no EXIF Orientation left to correct, and the
PDP stage then cover-cropped every photo into a 5:4 frame. Masters in this
folder are the prepared upright files (no Orientation tag). This script:

  * applies ImageOps.exif_transpose once, so a real Orientation tag is baked
    into pixels and an untagged upright file is not rotated
  * scales the long edge only (no stretch, no crop)
  * writes redesign/shared/products/<handle>-N.jpg and the -t thumbnail
  * rewrites that product's gallery markup, width/height, and shop-card frame

Run: python3 tools/prep_gallery.py
Also invoked at the start of tools/prep_redesign_images.py.
"""
import html, io, json, os, re, sys
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GALLERY = os.path.join(ROOT, "orig", "gallery")
OUT = os.path.join(ROOT, "redesign", "shared", "products")
SIZES = os.path.join(OUT, "sizes.json")
CSS = os.path.join(ROOT, "redesign", "v4", "style.css")
FRAME_JS = """<script>
/* ornament-gallery-frame: stage ratio follows the selected photo so the whole ornament, bow, and box stay visible */
(function () {
  var frame = document.querySelector(".rd-pdp__main");
  var main = document.querySelector("[data-rd-main]");
  if (!frame || !main) return;
  function show(src, w, h, alt) {
    if (src) main.src = src;
    if (w && h) { main.width = +w; main.height = +h; frame.style.setProperty("--rd-frame", w + " / " + h); }
    if (alt) main.alt = alt;
    if (!src) return;
    document.querySelectorAll("[data-rd-thumb]").forEach(function (t) {
      if (t.getAttribute("data-rd-thumb") === src) t.setAttribute("aria-current", "true");
      else t.removeAttribute("aria-current");
    });
  }
  document.querySelectorAll("[data-rd-thumb][data-w]").forEach(function (t) {
    t.addEventListener("click", function () {
      show(t.getAttribute("data-rd-thumb"), t.getAttribute("data-w"), t.getAttribute("data-h"), t.getAttribute("data-alt"));
    });
  });
  document.querySelectorAll('input[name="variant"][data-w]').forEach(function (r) {
    r.addEventListener("change", function () {
      if (r.checked) show(r.getAttribute("data-img"), r.getAttribute("data-w"), r.getAttribute("data-h"), r.getAttribute("data-alt"));
    });
  });
})();
</script>
"""


def normalize(im):
    """Bake EXIF orientation into pixels. Untagged images stay as stored."""
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def fit_long(im, max_edge):
    w, h = im.size
    long = max(w, h)
    if long <= max_edge:
        return im.copy()
    if w >= h:
        nw, nh = max_edge, max(1, round(h * max_edge / w))
    else:
        nh, nw = max_edge, max(1, round(w * max_edge / h))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def save_jpeg(im, path, q):
    im.save(path, format="JPEG", quality=q, optimize=True, progressive=True)


def mean_abs(a, b):
    if a.size != b.size:
        return 999
    aa = a.resize((48, 48), Image.Resampling.BOX)
    bb = b.resize((48, 48), Image.Resampling.BOX)
    pa, pb = aa.load(), bb.load()
    acc = 0
    for y in range(48):
        for x in range(48):
            p, q = pa[x, y], pb[x, y]
            acc += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])
    return acc / (48 * 48 * 3)


def self_test():
    """Untagged pixels are left alone. Orientation 6 is applied once, then stable."""
    port = Image.new("RGB", (20, 40), (10, 20, 30))
    for y in range(6):
        for x in range(6):
            port.putpixel((x, y), (255, 0, 0))
    buf = io.BytesIO()
    port.save(buf, format="JPEG", quality=95)
    buf.seek(0)
    fixed = normalize(Image.open(buf))
    assert fixed.size == (20, 40), fixed.size
    px = fixed.getpixel((2, 2))
    assert px[0] > 200 and px[1] < 40 and px[2] < 40, px
    assert normalize(fixed).size == (20, 40)

    land = Image.new("RGB", (40, 20), (0, 0, 80))
    for y in range(6):
        for x in range(6):
            land.putpixel((x, y), (0, 255, 0))
    exif = land.getexif()
    exif[274] = 6
    buf = io.BytesIO()
    land.save(buf, format="JPEG", quality=95, exif=exif)
    buf.seek(0)
    tagged = Image.open(buf)
    assert tagged.size == (40, 20)
    assert tagged.getexif().get(274) == 6
    once = normalize(tagged)
    assert once.size == (20, 40), once.size
    # Orientation 6 rotates the stored buffer 90° clockwise: the raw top-left lands on the right.
    moved = once.getpixel((once.width - 3, 2))
    assert moved[1] > 200 and moved[0] < 40, moved
    twice = normalize(once)
    assert twice.size == once.size
    print("orientation self-test ok")


def patch_sizes(entries):
    data = json.loads(open(SIZES, encoding="utf-8").read()) if os.path.exists(SIZES) else {}
    data.update(entries)
    raw = open(SIZES, encoding="utf-8").read() if os.path.exists(SIZES) else ""
    one_line = raw.strip().endswith("}") and "\n" not in raw.strip()
    # keep the historical one-line file; insert or replace only these keys
    if one_line:
        body = raw.strip()
        if not body.endswith("}"):
            raise SystemExit("sizes.json is not a JSON object")
        body = body[:-1].rstrip()
        for key in entries:
            body = re.sub(r',?\s*"%s"\s*:\s*\[[^\]]*\]' % re.escape(key), "", body)
        bits = ", ".join('"%s": %s' % (k, json.dumps(v, separators=(", ", ": "))) for k, v in entries.items())
        if body.endswith("{"):
            body = body + bits + "}\n"
        else:
            body = body + ", " + bits + "}\n"
        json.loads(body)
        open(SIZES, "w", encoding="utf-8").write(body)
    else:
        open(SIZES, "w", encoding="utf-8").write(json.dumps(data, indent=1) + "\n")


def gallery_html(handle, title, frames, initial):
    fr0 = frames[initial]
    w, h = fr0["full"]
    alt = html.escape(fr0.get("alt") or title, quote=True)
    main = (
        f'<div class="rd-pdp__main" style="--rd-frame:{w} / {h}">'
        f'<img src="/redesign/shared/products/{handle}-{initial}.jpg" alt="{alt}" width="{w}" height="{h}" '
        f'fetchpriority="high" data-rd-img data-rd-main></div>'
    )
    buttons = []
    for i, fr in enumerate(frames):
        fw, fh = fr["full"]
        tw, th = fr["thumb"]
        cur = ' aria-current="true"' if i == initial else ""
        ialt = html.escape(fr.get("alt") or "", quote=True)
        buttons.append(
            f'<button type="button" class="rd-thumb" style="--rd-frame:{tw} / {th}" '
            f'data-rd-thumb="/redesign/shared/products/{handle}-{i}.jpg" data-w="{fw}" data-h="{fh}" data-alt="{ialt}" '
            f'aria-label="Show image {i + 1}"{cur}>'
            f'<img src="/redesign/shared/products/{handle}-{i}-t.jpg" alt="" width="{tw}" height="{th}" loading="lazy"></button>'
        )
    thumbs = '<div class="rd-thumbs" role="group" aria-label="Product images">' + "".join(buttons) + "</div>"
    return main + "\n    " + thumbs


def patch_product(handle, title, frames):
    path = os.path.join(ROOT, "products", handle + ".html")
    html = open(path, encoding="utf-8").read()
    if re.search(r"<video\b|\.mp4\b|\.webm\b|\.mov\b", html, re.I):
        raise SystemExit(f"{handle}: video is not part of this card")
    html = html.replace('class="rd rd-v4 rd-page--product"', 'class="rd rd-v4 rd-page--product rd-pdp-ornaments"', 1)
    html = html.replace(" rd-pdp-ornaments rd-pdp-ornaments", " rd-pdp-ornaments")
    block = gallery_html(handle, title, frames, frames[0].get("_initial", 0))
    html2, n = re.subn(
        r'<div class="rd-pdp__main"[^>]*>.*?</div>\s*<div class="rd-thumbs"[^>]*>.*?</div>',
        block,
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"gallery markup not found in {path}")
    html2 = html2.replace("/redesign/v4/style.css?v=20261101h", "/redesign/v4/style.css?v=20261105a")
    if "ornament-gallery-frame" not in html2:
        html2 = html2.replace("</body>", FRAME_JS + "</body>", 1)
    else:
        html2 = re.sub(r"<script>\s*/\* ornament-gallery-frame:.*?</script>", FRAME_JS.strip(), html2, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(html2)


def patch_shop(handle, title, full, index):
    path = os.path.join(ROOT, "shop.html")
    if not os.path.exists(path):
        return
    html_doc = open(path, encoding="utf-8").read()
    w, h = full
    new = (
        f'<a class="rd-card__media" '
        f'href="/products/{handle}.html"><img src="/redesign/shared/products/{handle}-{index}.jpg" '
        f'alt="{html.escape(title, quote=True)}" width="{w}" height="{h}" loading="lazy" decoding="async" data-rd-img></a>'
    )
    html2, n = re.subn(
        r'<a class="rd-card__media[^"]*" (?:style="[^"]*" )?href="/products/%s\.html"><img src="/redesign/shared/products/%s-\d+\.jpg"[^>]*></a>'
        % (handle, handle),
        new,
        html_doc,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"shop card not found for {handle}")
    html2 = html2.replace("/redesign/v4/style.css?v=20261101h", "/redesign/v4/style.css?v=20261105a")
    open(path, "w", encoding="utf-8").write(html2)


def build_one(folder):
    manifest = json.load(open(os.path.join(folder, "manifest.json"), encoding="utf-8"))
    handle = manifest["handle"]
    title = manifest["title"]
    max_edge = int(manifest.get("max_edge", 1600))
    thumb_edge = int(manifest.get("thumb_edge", 240))
    require_portrait = bool(manifest.get("require_portrait", False))
    frames = []
    entries = {}
    images = []
    for item in manifest["images"]:
        if isinstance(item, str):
            images.append((item, ""))
        else:
            images.append((item["file"], item.get("alt") or ""))
    initial = int(manifest.get("initial_index", 0))
    if not 0 <= initial < len(images):
        raise SystemExit(f"{handle}: initial_index {initial} is outside the gallery")
    for i, (name, alt) in enumerate(images):
        src_path = os.path.join(folder, name)
        raw = Image.open(src_path)
        orient = raw.getexif().get(274)
        im = normalize(raw)
        if require_portrait and im.width >= im.height:
            raise SystemExit(f"{name}: expected an upright portrait after orientation normalize, got {im.size} (exif {orient})")
        full = fit_long(im, max_edge)
        thumb = fit_long(im, thumb_edge)
        # aspect must survive the resize (1px rounding only)
        for label, out in (("full", full), ("thumb", thumb)):
            if abs((out.width / out.height) - (im.width / im.height)) > 0.01:
                raise SystemExit(f"{name} {label} aspect drifted: {im.size} -> {out.size}")
        ref = im.resize(full.size, Image.Resampling.LANCZOS) if im.size != full.size else im
        err = mean_abs(ref, full)
        if err > 25:
            raise SystemExit(f"{name}: output does not match the upright master (mean abs {err:.1f})")
        if full.getexif().get(274) not in (None, 1):
            raise SystemExit(f"{name}: output still carries an Orientation tag")
        full_path = os.path.join(OUT, f"{handle}-{i}.jpg")
        thumb_path = os.path.join(OUT, f"{handle}-{i}-t.jpg")
        save_jpeg(full, full_path, 86)
        save_jpeg(thumb, thumb_path, 82)
        # reopen to confirm the file on disk stayed upright and untagged
        disk = Image.open(full_path)
        if disk.size != full.size or disk.getexif().get(274) not in (None, 1):
            raise SystemExit(f"{name}: saved file {disk.size} exif {disk.getexif().get(274)}")
        if require_portrait and disk.width >= disk.height:
            raise SystemExit(f"{name}: saved file is not portrait")
        frames.append({"full": full.size, "thumb": thumb.size, "src": im.size, "exif": orient, "alt": alt, "_initial": initial})
        entries[f"{handle}-{i}"] = [im.width, im.height, full.width, full.height]
        print(f"{handle}-{i} src {im.size} exif {orient} -> {full.size} thumb {thumb.size} err {err:.2f}")
    # drop a previous extra slot (the loose-plaid pair lived in slots 1 and 2; nothing past the manifest stays)
    for extra in os.listdir(OUT):
        m = re.fullmatch(rf"{re.escape(handle)}-(\d+)(-t)?\.jpg", extra)
        if m and int(m.group(1)) >= len(frames):
            os.remove(os.path.join(OUT, extra))
            print("removed obsolete", extra)
    patch_sizes(entries)
    patch_product(handle, title, frames)
    patch_shop(handle, title, frames[initial]["full"], initial)
    css = open(CSS, encoding="utf-8").read()
    if "rd-pdp-ornaments" not in css or "rd-card__media--full" not in css:
        raise SystemExit("redesign/v4/style.css is missing the ornament gallery frame rules")
    page = open(os.path.join(ROOT, "products", handle + ".html"), encoding="utf-8").read()
    if re.search(r"<video\b|\.mp4\b|\.webm\b|\.mov\b", page, re.I):
        raise SystemExit("video slipped into the product page")
    return handle, frames


def main():
    os.chdir(ROOT)
    self_test()
    if not os.path.isdir(GALLERY):
        print("no orig/gallery")
        return
    built = []
    for name in sorted(os.listdir(GALLERY)):
        folder = os.path.join(GALLERY, name)
        if os.path.isdir(folder) and os.path.exists(os.path.join(folder, "manifest.json")):
            built.append(build_one(folder)[0])
    if not built:
        print("no gallery manifests")
    else:
        print("galleries", ", ".join(built))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(1)
