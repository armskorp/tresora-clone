"""Headless TEST-MODE payment on Stripe's hosted checkout page with card 4242 4242 4242 4242.
usage:
  python3 tools/test_stripe_pay.py session  SITE_URL CHECKOUT_URL   # cart -> Worker -> Checkout Session -> pay
  python3 tools/test_stripe_pay.py link     SITE_URL                # product page "Buy now" -> Payment Link -> pay
  python3 tools/test_stripe_pay.py cart     SITE_URL                # main site: add to cart -> cart.html Checkout -> Payment Link -> pay
Screenshots: screenshots/stripe-<mode>-*.png"""
import asyncio, sys, re
from playwright.async_api import async_playwright
MODE, SITE = sys.argv[1], sys.argv[2].rstrip("/") + "/"
CHECKOUT_URL = sys.argv[3] if len(sys.argv) > 3 else ""
SHOT = f"screenshots/stripe-{MODE}"

async def fill_if(page, sel, val):
    loc = page.locator(sel)
    if await loc.count() and await loc.first.is_visible():
        await loc.first.fill(val); return True
    return False

async def pay(pg):
    await pg.wait_for_url(re.compile(r"https://(checkout|buy)\.stripe\.com/.*"), timeout=30000)
    await pg.wait_for_selector("#email", timeout=30000); await pg.wait_for_timeout(1500)
    await pg.screenshot(path=f"{SHOT}-1-checkout.png", full_page=True)
    await pg.fill("#email", "test+tresora@example.com")
    # card section (some layouts hide card fields behind a "Card" accordion)
    manual = pg.get_by_text("Enter address manually")
    if await manual.count() and await manual.first.is_visible(): await manual.first.click(); await pg.wait_for_timeout(500)
    if not await pg.locator("#cardNumber").is_visible():
        await pg.locator("[data-testid='card-accordion-item-button']").first.dispatch_event("click"); await pg.wait_for_timeout(1200)
    await pg.fill("#cardNumber", "4242424242424242")
    await pg.fill("#cardExpiry", "12 / 34")
    await pg.fill("#cardCvc", "123")
    await fill_if(pg, "#billingName", "Test Customer")
    await fill_if(pg, "#shippingName", "Test Customer")
    if await pg.locator("#shippingCountry").count():
        try: await pg.select_option("#shippingCountry", "US")
        except Exception: pass
    await fill_if(pg, "#shippingAddressLine1", "354 Oyster Point Blvd")
    # Google autocomplete dropdown may appear; dismiss it
    await pg.keyboard.press("Escape")
    await fill_if(pg, "#shippingLocality", "South San Francisco")
    await fill_if(pg, "#shippingPostalCode", "94080")
    if await pg.locator("#shippingAdministrativeArea").count():
        try: await pg.select_option("#shippingAdministrativeArea", "CA")
        except Exception: pass
    await fill_if(pg, "#billingPostalCode", "94080")
    # opt out of Link account creation if offered
    cb = pg.locator("#enableStripePass")
    if await cb.count() and await cb.is_checked(): await cb.uncheck()
    await pg.screenshot(path=f"{SHOT}-2-filled.png", full_page=True)
    await pg.click(".SubmitButton, button[type=submit]")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": 1280, "height": 900}, locale="en-US")
        pg = await ctx.new_page()
        if MODE == "session":
            async def cfg(route):
                await route.fulfill(content_type="application/javascript",
                    body='window.TRESORA_CONFIG={CHECKOUT_URL:%r,PAYMENT_LINKS:"",CURRENCY:"USD",MAX_QTY_PER_LINE:20};' % CHECKOUT_URL)
            await pg.route("**/assets/js/config.js", cfg)
            await pg.goto(SITE, wait_until="load")
            await pg.evaluate("localStorage.clear(); TresoraCart.add(44325276582001,2); TresoraCart.add(44325380423793,1);")
            await pg.evaluate("TRESORA_CATALOG.variants['44325276582001'].price = 1")  # client tampering must not matter
            await pg.evaluate("TresoraCart.open()"); await pg.wait_for_timeout(400)
            await pg.click("[data-tc-checkout]")
        elif MODE == "cart":
            await pg.goto(SITE + "products/klimt-the-kiss-gift-box.html", wait_until="load")
            await pg.evaluate("localStorage.clear()"); await pg.reload(wait_until="load")
            await pg.click("[data-rd-add]"); await pg.wait_for_timeout(500)
            await pg.goto(SITE + "cart.html", wait_until="load"); await pg.click("[data-rd-checkout]")
        else:
            await pg.goto(SITE + "products/klimt-the-kiss-gift-box.html", wait_until="load")
            await pg.click("[data-buy-now-link]")
        await pay(pg)
        try:
            await pg.wait_for_url(re.compile(r".*/success\.html\?session_id=cs_test_.*"), timeout=60000)
        except Exception:
            await pg.screenshot(path=f"{SHOT}-error.png", full_page=True); print("FAILED; url:", pg.url); await b.close(); sys.exit(1)
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=f"{SHOT}-3-success.png")
        print("PAID; landed on", pg.url)
        print("success page:", await pg.evaluate("({v4:document.documentElement.classList.contains('rd-v4'),h1:document.querySelector('h1')&&document.querySelector('h1').textContent,cart:JSON.parse(localStorage.getItem('tresora_cart_v1')||'[]').length})"))
        print("SESSION_ID", re.search(r"session_id=(cs_test_[A-Za-z0-9]+)", pg.url).group(1))
        await b.close()
asyncio.run(main())
