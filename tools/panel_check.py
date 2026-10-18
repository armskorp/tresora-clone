"""Open-panel behaviour on the main site: mobile menu, mobile search, cart drawer close on outside tap / backdrop,
Escape and browser back; links inside panels still navigate.  usage: python3 tools/panel_check.py SITE_ROOT"""
import asyncio, sys
from playwright.async_api import async_playwright
BASE = sys.argv[1].rstrip("/") + "/"
CLS = "document.documentElement.classList.contains(%r)"

async def run(p, engine, mobile):
    mobile = mobile in (True, "m")
    if engine == "webkit":
        b = await p.webkit.launch(); ctx = await b.new_context(**(p.devices["iPhone 14"] if mobile else {"viewport": {"width": 1280, "height": 800}}))
    else:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = await b.new_context(**({"viewport": {"width": 390, "height": 844}, "is_mobile": True, "has_touch": True, "device_scale_factor": 3} if mobile else {"viewport": {"width": 1280, "height": 800}}))
    pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    tap = (lambda x, y: pg.touchscreen.tap(x, y)) if mobile else (lambda x, y: pg.mouse.click(x, y))
    res = {}
    async def is_on(c): await pg.wait_for_timeout(350); return await pg.evaluate(CLS % c)
    async def back_closes(open_js, c):
        url = pg.url; await open_js(); assert await is_on(c), f"{c} did not open"
        await pg.go_back(wait_until="commit"); await pg.wait_for_timeout(500)
        return (not await pg.evaluate(CLS % c)) and pg.url == url
    await pg.goto(BASE + "shop.html", wait_until="load"); await pg.evaluate("localStorage.clear()")
    await pg.goto(BASE + "products/paris-gift-box.html", wait_until="load")
    await pg.click("[data-rd-add]"); await pg.wait_for_timeout(500)          # opens the drawer with 1 item
    res["cart_opened_by_add"] = await is_on("tc-open")
    await tap(20, 420); res["cart_overlay_tap"] = not await is_on("tc-open")
    async def open_cart(): await pg.click("[data-cart-open]")
    await open_cart(); await is_on("tc-open"); await pg.keyboard.press("Escape"); res["cart_escape"] = not await is_on("tc-open")
    res["cart_back"] = await back_closes(open_cart, "tc-open")
    await open_cart(); await is_on("tc-open")
    async with pg.expect_navigation(): await pg.click(".tc-items a.tc-item__title")
    res["cart_link_navigates"] = pg.url.endswith("/products/paris-gift-box.html")
    if mobile:
        async def open_menu(): await pg.click("[data-rd-menu]")
        await open_menu(); res["menu_opened"] = await is_on("rd-menu-open")
        res["backdrop_visible"] = await pg.evaluate("getComputedStyle(document.querySelector('.rd-backdrop')).visibility === 'visible'")
        await tap(200, 800); res["menu_backdrop_tap"] = not await is_on("rd-menu-open")
        await open_menu(); await is_on("rd-menu-open"); await pg.keyboard.press("Escape"); res["menu_escape"] = not await is_on("rd-menu-open")
        res["menu_back"] = await back_closes(open_menu, "rd-menu-open")
        await open_menu(); await is_on("rd-menu-open"); await tap(100, 30)   # empty header area outside the menu list
        res["menu_outside_header_tap"] = not await pg.evaluate(CLS % "rd-menu-open")
        if pg.url.endswith("/products/paris-gift-box.html") is False: await pg.goto(BASE + "products/paris-gift-box.html", wait_until="load")
        await open_menu(); await is_on("rd-menu-open")
        async with pg.expect_navigation(): await pg.click(".rd-nav a[href$='shop.html']")
        await pg.wait_for_timeout(600); res["menu_link_navigates"] = pg.url.endswith("/shop.html")
        async def open_search(): await pg.click("[data-rd-searchtoggle]")
        await open_search(); res["search_opened"] = await is_on("rd-searching")
        await tap(200, 800); res["search_backdrop_tap"] = not await is_on("rd-searching")
        await open_search(); await is_on("rd-searching"); await pg.keyboard.press("Escape"); res["search_escape"] = not await is_on("rd-searching")
        res["search_back"] = await back_closes(open_search, "rd-searching")
    else:
        await pg.fill("[data-rd-q]", "pa"); await pg.wait_for_timeout(400)
        res["suggest_open"] = await pg.is_visible("[data-rd-suggest]")
        await pg.mouse.click(640, 600); await pg.wait_for_timeout(300); res["suggest_outside_click"] = not await pg.is_visible("[data-rd-suggest]")
    res["no_js_errors"] = not errs
    bad = [k for k, v in res.items() if v is not True]
    print(("PASS " if not bad else "FAIL ") + f"{engine}/{'390' if mobile else '1280'} " + (" ".join(bad) if bad else f"{len(res)} checks"), flush=True)
    await b.close(); return not bad

async def main():
    async with async_playwright() as p:
        ok = [await run(p, e, m) for e, m in ([tuple(x.split(":")) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [(e, m) for e in ("chromium", "webkit") for m in (False, True)])]
    print(f"{sum(ok)}/{len(ok)} PASS"); sys.exit(0 if all(ok) else 1)
asyncio.run(main())
