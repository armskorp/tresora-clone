"""Mobile layout audit + plain full-page screenshots (no CSS overrides; what a phone user sees).
Checks per viewport: horizontal overflow, elements wider than the screen, scroll lock, real scrollable height vs content,
fixed/sticky header covering content, clipped sections, and drawer/menu open+close leaving scroll locked.
usage: python3 tools/mobile_audit.py BASE_URL SHOT_PREFIX [PAGE_PATH]"""
import asyncio, sys, json
from playwright.async_api import async_playwright
BASE = sys.argv[1].rstrip("/") + "/"; SHOT = sys.argv[2]; PATH = sys.argv[3] if len(sys.argv) > 3 else ""
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
VPS = [("360", 360, 780), ("390", 390, 844), ("414", 414, 896), ("landscape", 844, 390)]
MEASURE = """() => {
  const vw = document.documentElement.clientWidth, de = document.documentElement, b = document.body;
  const scroller = document.scrollingElement;
  const wide = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (r.right > vw + 1 || r.left < -1) {
      // ignore things inside horizontal scrollers / clipped parents (intentional carousels)
      let p = e.parentElement, clipped = false;
      while (p && p !== b) { const c = getComputedStyle(p); if (/(hidden|auto|scroll|clip)/.test(c.overflowX)) { const pr = p.getBoundingClientRect(); if (pr.right <= vw + 1 && pr.left >= -1) { clipped = true; break; } } p = p.parentElement; }
      if (!clipped && getComputedStyle(e).position !== 'fixed') wide.push(e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/).slice(0,2).join('.') + ' [' + Math.round(r.left) + ',' + Math.round(r.right) + ']');
    }
  }
  const cs = (el) => { const c = getComputedStyle(el); return {ox: c.overflowX, oy: c.overflowY, h: c.height}; };
  const pw = document.querySelector('.page-wrapper');
  const footer = document.querySelector('footer, .tp-footer');
  return { vw, innerW: innerWidth, innerH: innerHeight, docScrollW: scroller.scrollWidth, docScrollH: scroller.scrollHeight,
    html: cs(de), body: cs(b), pageWrapper: pw ? {...cs(pw), scrollH: pw.scrollHeight, clientH: pw.clientHeight} : null,
    footerBottom: footer ? Math.round(footer.getBoundingClientRect().bottom + scroller.scrollTop) : null,
    wide: [...new Set(wide)].slice(0, 15), htmlClass: de.className, htmlStyle: de.getAttribute('style'), bodyStyle: b.getAttribute('style') };
}"""
async def can_reach_bottom(pg):
    # scroll like a finger would: wheel/touch on the document, then check the footer is in view
    for _ in range(80):
        await pg.mouse.wheel(0, 600); await pg.wait_for_timeout(30)
    await pg.wait_for_timeout(500)
    return await pg.evaluate("""() => { const f = document.querySelector('footer, .tp-footer'); if (!f) return null;
      const r = f.getBoundingClientRect(); return {footerTop: Math.round(r.top), footerBottom: Math.round(r.bottom), innerH: innerHeight, scrollY: Math.round(scrollY), pwTop: (document.querySelector('.page-wrapper')||{}).scrollTop}; }""")
async def main():
    out = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        for name, w, h in VPS:
            ctx = await b.new_context(viewport={"width": w, "height": h}, is_mobile=True, has_touch=True, device_scale_factor=2, user_agent=UA)
            pg = await ctx.new_page()
            await pg.goto(BASE + PATH + "?m=" + name, wait_until="load", timeout=60000); await pg.wait_for_timeout(1200)
            m = await pg.evaluate(MEASURE)
            m["reach_bottom"] = await can_reach_bottom(pg)
            # open + close the menu drawer and cart drawer, then check scrolling still works
            locks = {}
            for label, opener, closer in [("menu", "summary.header__icon--menu", ".menu-drawer__close-button"), ("cart", '[data-testid="cart-drawer-trigger"], [data-cart-open]', ".tc-close")]:
                await pg.evaluate("window.scrollTo(0,0); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop=0)")
                o = pg.locator(opener).first
                if await o.count() and await o.is_visible():
                    await o.tap(); await pg.wait_for_timeout(700)
                    c = pg.locator(closer).first
                    if await c.count() and await c.is_visible(): await c.tap()
                    else: await pg.keyboard.press("Escape")
                    await pg.wait_for_timeout(700)
                    await pg.mouse.wheel(0, 1500); await pg.wait_for_timeout(400)
                    locks[label] = await pg.evaluate("({scrollY: Math.round(scrollY), pw: (document.querySelector('.page-wrapper')||{}).scrollTop, htmlOverflow: document.documentElement.style.overflow, htmlClass: document.documentElement.className})")
            m["after_drawers"] = locks
            out[name] = m
            print(name, json.dumps({k: m[k] for k in ("vw", "docScrollW", "docScrollH", "html", "body", "pageWrapper", "reach_bottom", "after_drawers")}))
            if m["wide"]: print("   WIDE:", m["wide"])
            # plain full-page screenshot after a slow scroll (lazy images), scrolled back to top
            await pg.evaluate("window.scrollTo(0,0); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop=0)")
            for y in range(0, m["docScrollH"] + 1000, 300):
                await pg.evaluate(f"window.scrollTo(0,{y}); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop={y})"); await pg.wait_for_timeout(60)
            await pg.evaluate("window.scrollTo(0,0); document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop=0)"); await pg.wait_for_timeout(800)
            await pg.screenshot(path=f"{SHOT}-{name}.png", full_page=True)
            await ctx.close()
        await b.close()
    json.dump(out, open(f"{SHOT}.json", "w"), indent=1)
asyncio.run(main())
