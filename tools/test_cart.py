"""Headless end-to-end test of the client-side cart.  usage: python3 tools/test_cart.py [BASE_URL] [SHOT_PREFIX]"""
import asyncio, sys, json
from playwright.async_api import async_playwright, expect
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765/").rstrip("/") + "/"
SHOT = sys.argv[2] if len(sys.argv) > 2 else "screenshots/cart"
results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))

async def state(pg):
    return await pg.evaluate("({count: TresoraCart.count(), subtotal: TresoraCart.subtotal(), items: TresoraCart.items(), bubble: (document.querySelector('cart-icon .cart-bubble__text-count')||document.querySelector('[data-cart-count]')||{}).textContent})")

async def desktop(b):
    ctx = await b.new_context(viewport={"width": 1280, "height": 800}); pg = await ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(BASE, wait_until="load"); await pg.evaluate("localStorage.clear()"); await pg.reload(wait_until="load")
    s = await state(pg); check("desktop: empty cart on first visit", s["count"] == 0 and s["items"] == [])
    # empty drawer
    await pg.click('[data-testid="cart-drawer-trigger"]'); await pg.wait_for_timeout(500)
    check("desktop: cart icon opens drawer (empty state)", await pg.is_visible("text=Your cart is empty"))
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400)
    # homepage card Add (Klimt, single variant)
    card = pg.locator("product-card", has_text="Klimt The Kiss Gift Box").first
    await card.scroll_into_view_if_needed(); await card.hover(); await pg.wait_for_timeout(400)
    await card.locator(".quick-add__button--add").click(); await pg.wait_for_timeout(600)
    s = await state(pg); check("desktop: homepage card 'Add' adds item", s["count"] == 1 and s["subtotal"] == 5900, s)
    check("desktop: header bubble shows 1", (s["bubble"] or "").strip() == "1", s["bubble"])
    check("desktop: drawer opened after add", await pg.evaluate("document.documentElement.classList.contains('tc-open')"))
    await pg.click(".tc-item [data-tc-inc]"); await pg.wait_for_timeout(200)
    s = await state(pg); check("desktop: + increments qty", s["count"] == 2 and s["subtotal"] == 11800, s)
    check("desktop: subtotal text", (await pg.text_content("[data-tc-subtotal]")).strip() == "$118.00 USD")
    await pg.screenshot(path=f"{SHOT}-desktop-drawer.png")
    await pg.click(".tc-item [data-tc-dec]"); await pg.wait_for_timeout(200)
    s = await state(pg); check("desktop: − decrements qty", s["count"] == 1, s)
    await pg.keyboard.press("Escape")
    # "Choose" card (Caravaggio has colour options) -> product page
    card = pg.locator("product-card", has_text="Caravaggio Bacchus Wine Gift Box").first
    await card.scroll_into_view_if_needed(); await card.hover(); await pg.wait_for_timeout(400)
    ch = card.locator(".quick-add__button--choose")
    if await ch.is_visible():
        await ch.click()
    else:
        await card.locator("a[href*='products/']").first.click()
    await pg.wait_for_load_state("load")
    check("desktop: 'Choose' goes to product page", "caravaggio-bacchus-wine-gift-box.html" in pg.url, pg.url)
    s = await state(pg); check("desktop: cart persisted across pages", s["count"] == 1, s)
    await pg.click("text=Red"); await pg.click("[data-step='1']"); await pg.click("[data-step='1']")
    check("desktop: product price shown", (await pg.text_content("[data-variant-price]")).strip() == "$69.00 USD")
    await pg.click(".tp-add"); await pg.wait_for_timeout(600)
    s = await state(pg)
    check("desktop: product page adds variant Red x3", any(i["variant_id"] == 44325380423793 and i["quantity"] == 3 for i in s["items"]) and s["count"] == 4, s)
    check("desktop: subtotal 59 + 3*69 = 266", s["subtotal"] == 26600, s)
    await pg.screenshot(path=f"{SHOT}-desktop-product-drawer.png")
    await pg.reload(wait_until="load")
    s = await state(pg); check("desktop: reload keeps cart", s["count"] == 4 and s["subtotal"] == 26600, s)
    await pg.click("[data-cart-open]"); await pg.wait_for_timeout(400)
    await pg.click("[data-tc-checkout]"); await pg.wait_for_timeout(300)
    m = await pg.text_content("[data-tc-msg]")
    check("desktop: checkout without CHECKOUT_URL shows 'coming soon'", "coming soon" in m.lower(), m)
    await pg.screenshot(path=f"{SHOT}-desktop-coming-soon.png")
    await pg.locator(".tc-item", has_text="Klimt").locator("[data-tc-remove]").click(); await pg.wait_for_timeout(200)
    s = await state(pg); check("desktop: remove deletes line", s["count"] == 3 and len(s["items"]) == 1, s)
    # sold-out product
    await pg.goto(BASE + "products/rococo-reverie-decorative-glass-bottle.html", wait_until="load")
    check("desktop: sold-out product cannot be added", await pg.is_disabled(".tp-add"))
    # tampering: bogus localStorage entries are dropped
    await pg.evaluate("localStorage.setItem('tresora_cart_v1', JSON.stringify([{variant_id:1,quantity:5},{variant_id:44325276582001,quantity:999}]))")
    await pg.reload(wait_until="load"); s = await state(pg)
    check("desktop: unknown variants dropped, qty clamped to 20", s["items"] == [{"variant_id": 44325276582001, "quantity": 20}], s)
    check("desktop: no JS errors", not errs, errs)
    await ctx.close()

async def mobile(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2); pg = await ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto(BASE, wait_until="load"); await pg.evaluate("localStorage.clear()"); await pg.reload(wait_until="load")
    card = pg.locator("product-card", has_text="Paris Gift Box").first
    await card.scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
    btn = card.locator(".quick-add__button--add")
    vis = await btn.is_visible(); check("mobile: card 'Add' button visible", vis)
    if vis: await btn.tap()
    else: await pg.evaluate("TresoraCart.add(44512196821105,1)")
    await pg.wait_for_timeout(600)
    s = await state(pg); check("mobile: added Paris", s["count"] == 1 and s["subtotal"] == 5900, s)
    await pg.goto(BASE + "products/vermeer-girl-with-a-pearl-earring-gift-box.html", wait_until="load")
    await pg.screenshot(path=f"{SHOT}-mobile-product.png")
    await pg.tap("text=White"); await pg.tap("[data-step='1']"); await pg.tap(".tp-add"); await pg.wait_for_timeout(700)
    s = await state(pg); check("mobile: product page add (White x2)", s["count"] == 3 and s["subtotal"] == 5900 + 2 * 6500, s)
    await pg.screenshot(path=f"{SHOT}-mobile-drawer.png")
    await pg.tap(".tc-close"); await pg.goto(BASE, wait_until="load")
    s = await state(pg); check("mobile: homepage bubble after navigation", (s["bubble"] or "").strip() == "3", s["bubble"])
    await pg.tap('[data-testid="cart-drawer-trigger"]'); await pg.wait_for_timeout(500)
    check("mobile: drawer opens from header", await pg.evaluate("document.documentElement.classList.contains('tc-open')"))
    await pg.screenshot(path=f"{SHOT}-mobile-home-drawer.png")
    check("mobile: no JS errors", not errs, errs)
    await ctx.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        await desktop(b); await mobile(b); await b.close()
    bad = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(bad)}/{len(results)} passed"); sys.exit(1 if bad else 0)
asyncio.run(main())
