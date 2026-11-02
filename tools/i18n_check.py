"""EN|ES switcher check: python3 tools/i18n_check.py BASE"""
import asyncio, sys, re, json
from playwright.async_api import async_playwright
B = sys.argv[1].rstrip("/") + "/"
PAGES = ["", "shop.html", "cart.html", "account.html", "success.html", "cancel.html", "products/paris-gift-box.html", "products/caravaggio-bacchus-wine-gift-box.html", "products/rococo-reverie-decorative-glass-bottle.html", "products/gothic-romance-decorative-glass-bottle.html", "products/elegant-pearl-earring-table-gift-box.html", "products/crow-roses-decorative-bottle.html", "products/gothic-portraits-decorative-glass-vase.html", "products/amalfi-gift-box.html", "contact.html", "shipping.html", "returns.html", "privacy.html", "terms.html", "about.html", "faq.html"]
BRAND = re.compile(r"^(TRESORA|© 2026 TRESORA|Instagram|Facebook|TikTok|Pinterest|Etsy|SueD|EN|ES|\||Amalfi|Barcelona|Caravaggio|Gothic Romance|Klimt.*|Vermeer.*|Van Gogh.*|John Sargent.*|Paris Gift Box|New York Gift Box|Amalfi Gift Box|Barcelona Gift Box|Caravaggio Bacchus Wine Gift Box|Elegant Girl.*|Gothic Romance Handcrafted.*|Gothic Portraits Handcrafted.*|Crow & Roses Handcrafted.*|Handcrafted Artisan Glass Bottle.*|.*\$[\d.,]+.*|USD|[\d\s.,:()+×−·$|%/-]+)$")
async def main():
    fails = 0
    async with async_playwright() as p:
        for mobile in (False, True):
            b = await p.chromium.launch(); ctx = await b.new_context(**(dict(p.devices["iPhone 14"]) if mobile else {"viewport": {"width": 1280, "height": 800}}))
            pg = await ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
            tag = "390" if mobile else "1280"
            await pg.goto(B); en_nav = await pg.locator("#rd-nav").inner_text()
            vis = await pg.locator(".rd-lang").is_visible(); ok = vis and await pg.locator(".rd-lang [data-lang=en]").get_attribute("aria-pressed") == "true"
            print(("PASS" if ok else "FAIL"), tag, "switcher visible, EN default"); fails += not ok
            await pg.screenshot(path=f"/tmp/qa/lang-{tag}-en.png")
            await pg.locator(".rd-lang [data-lang=es]").click(); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(600)
            await pg.screenshot(path=f"/tmp/qa/lang-{tag}-es.png")
            ow = await pg.evaluate("document.documentElement.scrollWidth-innerWidth"); print(("PASS" if ow <= 1 else "FAIL"), tag, "no overflow in ES header", ow); fails += ow > 1
            left = {}
            for u in PAGES:
                await pg.goto(B + u); await pg.wait_for_timeout(400)
                if u == "": await pg.locator("[data-rd-add]:not([disabled])").first.click(); await pg.wait_for_timeout(500)
                txt = await pg.evaluate("""()=>{const out=new Set();const w=document.createTreeWalker(document.body,4);let n;while(n=w.nextNode()){const p=n.parentElement;if(!p||p.closest('script,style,[hidden]'))continue;const s=n.nodeValue.replace(/\\s+/g,' ').trim();if(/[A-Za-z]{3}/.test(s))out.add(s)}document.querySelectorAll('[placeholder],[aria-label],[alt],[title]').forEach(e=>['placeholder','aria-label','alt','title'].forEach(a=>{const v=e.getAttribute(a);if(v&&/[A-Za-z]{3}/.test(v))out.add(v.trim())}));out.add(document.title);return [...out]}""")
                en = [s for s in txt if not BRAND.match(s) and re.search(r"\b(the|and|with|your|cart|shop|add|free|shipping|gift|sign|search|of|for|in|to)\b", s, re.I) and not re.search(r"[áéíóúñ¿¡]|\b(de|con|para|tu|el|la|los|las|y)\b", s)]
                if en: left[u] = en
                lang = await pg.evaluate("document.documentElement.lang")
                if lang != "es": print("FAIL", tag, u, "html lang", lang); fails += 1
            print(("PASS" if not left else "WARN"), tag, "untranslated English-looking strings:", json.dumps(left, ensure_ascii=False)[:1500])
            await pg.goto(B); es_nav = await pg.locator("#rd-nav").inner_text()
            ok = "ver todo" in es_nav.lower() and "reseñas" in es_nav.lower(); print(("PASS" if ok else "FAIL"), tag, "ES nav:", es_nav.replace("\n", " | ")[:120]); fails += not ok
            await pg.locator("[data-rd-add]:not([disabled])").first.click(); await pg.wait_for_timeout(800)
            if not await pg.locator(".tc-drawer").is_visible(): await pg.locator("[data-cart-open]").first.click(); await pg.wait_for_timeout(500)
            d = await pg.locator(".tc-drawer").inner_text(); ok = "Carrito" in d and "Pagar" in d; print(("PASS" if ok else "FAIL"), tag, "cart drawer ES"); fails += not ok
            await pg.screenshot(path=f"/tmp/qa/lang-{tag}-es-cart.png"); await pg.keyboard.press("Escape")
            await pg.locator(".rd-lang [data-lang=en]").click(); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(400)
            back = await pg.locator("#rd-nav").inner_text(); ok = back == en_nav and await pg.evaluate("document.documentElement.lang") == "en"
            print(("PASS" if ok else "FAIL"), tag, "back to EN restores English"); fails += not ok
            print(("PASS" if not errs else "FAIL"), tag, "JS errors", errs[:3]); fails += bool(errs)
            await b.close()
    print("FAILS", fails)
asyncio.run(main())
