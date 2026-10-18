"""Screenshots + checks for redesign/v1..v3 in Chromium and WebKit at 1280 and 390.
usage: python3 tools/redesign_check.py BASE_URL [--shots]"""
import asyncio, sys, json
from playwright.async_api import async_playwright
BASE = sys.argv[1].rstrip("/") + "/"; SHOTS = "--shots" in sys.argv
async def load_all(pg):
    h = await pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h + 800, 500):
        await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(60)
    await pg.evaluate("Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r;setTimeout(r,8000)})))")
    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(300)
async def run(p, engine, n, w, h, mobile):
    if engine == "webkit": b = await p.webkit.launch(); ctx = await b.new_context(**(p.devices["iPhone 14"] | {"viewport": {"width": w, "height": h}}) if mobile else {"viewport": {"width": w, "height": h}})
    else:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1)
    pg = await ctx.new_page(); errs = []; bad = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    await pg.goto(f"{BASE}redesign/v{n}/", wait_until="load", timeout=60000)
    await pg.evaluate("localStorage.clear()"); await pg.reload(wait_until="load")
    await load_all(pg)
    r = await pg.evaluate("""()=>({broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.getAttribute('src')),
      imgs:document.images.length, overflow:document.documentElement.scrollWidth-innerWidth, height:document.documentElement.scrollHeight,
      cards:document.querySelectorAll('.rd-card').length})""")
    if SHOTS and engine == "chromium":
        name = "mobile" if mobile else "desktop"
        await pg.screenshot(path=f"screenshots/redesign-v{n}-{name}.png", full_page=True)
        if not mobile: await pg.screenshot(path=f"screenshots/redesign-v{n}-hero.png")
    # interactions
    t = {}
    await pg.click(".rd-tab[data-rd-filter=city]"); t["filter_city"] = await pg.evaluate("[...document.querySelectorAll('.rd-card')].filter(c=>!c.hidden).length")
    await pg.click(".rd-tab[data-rd-filter=all]")
    btn = pg.locator(".rd-card[data-cat=city] [data-rd-add]").first
    await btn.scroll_into_view_if_needed(); await btn.click(); await pg.wait_for_timeout(500)
    t["cart_count"] = await pg.evaluate("document.querySelector('[data-cart-count]').textContent")
    t["drawer_open"] = await pg.evaluate("document.documentElement.classList.contains('tc-open')")
    if SHOTS and engine == "chromium": await pg.screenshot(path=f"screenshots/redesign-v{n}-{'mobile' if mobile else 'desktop'}-cart.png")
    await pg.keyboard.press("Escape"); await pg.evaluate("document.querySelectorAll('[data-cart-close]')[0]?.click()"); await pg.wait_for_timeout(400)
    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(200)
    if mobile: await pg.click("[data-rd-searchtoggle]")
    await pg.fill("[data-rd-q]", "klimt"); await pg.wait_for_timeout(250)
    t["search_hits"] = await pg.evaluate("document.querySelectorAll('[data-rd-suggest] a').length")
    await pg.press("[data-rd-q]", "Enter"); await pg.wait_for_timeout(300)
    t["search_grid"] = await pg.evaluate("[...document.querySelectorAll('.rd-card')].filter(c=>!c.hidden).length")
    await pg.evaluate("window.scrollTo(0,0)")
    await pg.locator(".rd-header [data-rd-account]").click(); await pg.wait_for_timeout(300)
    t["modal_open"] = await pg.evaluate("document.querySelector('[data-rd-modal]').open")
    await pg.click("[data-rd-tab=signup]"); await pg.fill(".rd-auth input[name=email]", "test@example.com"); await pg.fill(".rd-auth input[name=password]", "secret123")
    if SHOTS and engine == "chromium": await pg.screenshot(path=f"screenshots/redesign-v{n}-{'mobile' if mobile else 'desktop'}-signup.png")
    await pg.click("[data-rd-submit]"); t["signup_msg"] = (await pg.text_content(".rd-auth__msg"))[:40]
    await b.close()
    return {"engine": engine, "v": n, "w": w, **r, "errors": errs, "http_bad": bad, **t}
async def main():
    out = []
    async with async_playwright() as p:
        for n in (1, 2, 3):
            for engine in ("chromium", "webkit"):
                for w, h, m in ((1280, 800, False), (390, 844, True)):
                    res = await run(p, engine, n, w, h, m); out.append(res)
                    ok = not res["broken"] and res["overflow"] <= 0 and not res["errors"] and not res["http_bad"] and res["cart_count"] == "1" and res["modal_open"] and res["filter_city"] == 4 and res["search_hits"] >= 1
                    print(("PASS" if ok else "FAIL"), json.dumps(res)[:600])
    json.dump(out, open("/tmp/redesign_check.json", "w"), indent=1)
asyncio.run(main())
