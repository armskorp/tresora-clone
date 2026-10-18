"""Audit every <img> on the site (homepage + product + return pages) at 1280 and 390 widths.
Scrolls slowly (window and Horizon's .page-wrapper) to trigger lazy loading, then reports:
  - HTTP >= 400 responses for images
  - <img> with naturalWidth == 0 (broken or never loaded)
  - <img> inside product cards / heroes that are loaded but not visible (display:none, opacity 0, zero size)
usage: python3 tools/audit_images.py BASE_URL [OUT_JSON] [SHOT_PREFIX]"""
import asyncio, sys, json, re
from playwright.async_api import async_playwright
BASE = sys.argv[1].rstrip("/") + "/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/audit.json"
SHOT = sys.argv[3] if len(sys.argv) > 3 else None
HANDLES = ["amalfi-gift-box","barcelona-gift-box","caravaggio-bacchus-wine-gift-box","elegant-pearl-earring-table-gift-box",
 "gothic-romance-decorative-glass-bottle","klimt-the-kiss-gift-box","new-york-gift-box","paris-gift-box",
 "rococo-reverie-decorative-glass-bottle","sargent-the-wineglasses-wine-gift-box","van-gogh-almond-blossom-gift-box",
 "vermeer-girl-with-a-pearl-earring-gift-box"]
PAGES = [""] + [f"products/{h}.html" for h in HANDLES] + ["success.html", "cancel.html"]
JS = """() => [...document.images].map((i, n) => {
  const r = i.getBoundingClientRect(), cs = getComputedStyle(i);
  let hidden = null, e = i;
  while (e && e !== document.body) { const c = getComputedStyle(e);
    if (c.display === 'none') { hidden = 'display:none on ' + e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/)[0]; break; }
    if (c.visibility === 'hidden') { hidden = 'visibility:hidden on ' + e.tagName.toLowerCase(); break; }
    e = e.parentElement; }
  const card = i.closest('product-card, .product-card, .tc-item, .tp-media, .collection-card, .hero, .card-gallery');
  const slide = i.closest('slideshow-slide');
  return { n, src: i.getAttribute('src'), current: i.currentSrc, nw: i.naturalWidth, complete: i.complete, loading: i.loading,
    w: Math.round(r.width), h: Math.round(r.height), opacity: cs.opacity, hidden,
    inCard: !!card, cardTitle: card ? (card.querySelector('.product-card__title, h3, .title, a[class*=title]')||{}).textContent : null,
    slideHidden: slide ? slide.getAttribute('aria-hidden') : null, alt: i.alt };
})"""
async def scroll(pg):
    h = await pg.evaluate("Math.max(document.documentElement.scrollHeight, (document.querySelector('.page-wrapper')||{scrollHeight:0}).scrollHeight)")
    for y in range(0, h + 800, 250):
        await pg.evaluate(f"window.scrollTo(0,{y}); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop={y})")
        await pg.wait_for_timeout(90)
    await pg.wait_for_timeout(1500)
    # also swipe through every slideshow so non-first slides get a chance to load
    await pg.evaluate("document.querySelectorAll('slideshow-slides').forEach(t=>{t.scrollLeft=t.scrollWidth})")
    await pg.wait_for_timeout(1200)
    await pg.evaluate("document.querySelectorAll('slideshow-slides').forEach(t=>{t.scrollLeft=0}); window.scrollTo(0,0); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop=0)")
    await pg.wait_for_timeout(500)
async def main():
    report = []
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for label, w, h, mob in [("desktop", 1280, 800, False), ("mobile", 390, 844, True)]:
            ctx = await b.new_context(viewport={"width": w, "height": h}, is_mobile=mob, has_touch=mob)
            for path in PAGES:
                pg = await ctx.new_page(); bad = []
                pg.on("response", lambda r, bad=bad: bad.append((r.status, r.url)) if r.status >= 400 else None)
                pg.on("requestfailed", lambda r, bad=bad: bad.append(("failed", r.url)))
                url = BASE + path + ("?audit=1" if "?" not in path else "")
                await pg.goto(url, wait_until="load", timeout=60000); await pg.wait_for_timeout(800)
                await scroll(pg)
                imgs = await pg.evaluate(JS)
                broken = [i for i in imgs if i["nw"] == 0 and not i["hidden"]]
                broken_hidden = [i for i in imgs if i["nw"] == 0 and i["hidden"]]
                invisible_card = [i for i in imgs if i["inCard"] and i["nw"] > 0 and not i["hidden"] and (i["w"] == 0 or i["h"] == 0 or float(i["opacity"]) == 0) and i["slideHidden"] != "true"]
                report.append({"viewport": label, "page": path or "index", "images": len(imgs), "http_errors": bad,
                               "broken_visible": broken, "broken_in_hidden": broken_hidden, "invisible_in_card": invisible_card})
                print(f"{label:7} {path or 'index':55} imgs={len(imgs):3} http_err={len(bad)} broken={len(broken)} broken_hidden={len(broken_hidden)} invisible_card={len(invisible_card)}")
                if SHOT and path == "":
                    await pg.screenshot(path=f"{SHOT}-{label}-home.png", full_page=False)
                await pg.close()
            await ctx.close()
        await b.close()
    json.dump(report, open(OUT, "w"), indent=1)
asyncio.run(main())
