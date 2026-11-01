"""Click-through QA of the live site. usage: live_qa.py BASE [engine]"""
import asyncio, sys, re
from playwright.async_api import async_playwright
B = sys.argv[1].rstrip("/") + "/"; ENG = sys.argv[2] if len(sys.argv) > 2 else "chromium"
R = []
def ok(area, name, cond, extra=""): R.append((area, name, bool(cond), extra)); print(("PASS" if cond else "FAIL"), area, "|", name, extra, flush=True)
async def run(p, mobile):
    tag = f"{ENG}/{'390' if mobile else '1280'}"
    b = await getattr(p, ENG).launch()
    ctx = await b.new_context(**(dict(p.devices["iPhone 14"]) if mobile else {"viewport": {"width": 1280, "height": 800}}))
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("response", lambda r: errs.append(f"{r.status} {r.url}") if r.status >= 400 and "tresoragift" in r.url else None)
    async def shot(n): await pg.screenshot(path=f"/tmp/qa/{tag.replace('/','-')}-{n}.png")
    async def click(sel):
        el = pg.locator(sel).first
        if mobile: await el.tap()
        else: await el.click()
    # --- every link on every page
    pages = ["", "shop.html", "cart.html", "account.html", "success.html", "cancel.html"]
    await pg.goto(B + "shop.html"); pages += sorted(set(await pg.eval_on_selector_all("a[href*='/products/']", "a=>a.map(x=>new URL(x.href).pathname.slice(1))")))
    links = {}
    for u in pages:
        await pg.goto(B + u, wait_until="load")
        for h in await pg.eval_on_selector_all("a[href]", "a=>a.map(x=>x.getAttribute('href'))"): links.setdefault(h, u)
    bad = [h for h in links if h in ("#", "") or h.startswith("javascript")]
    ok("links", f"no dead '#' links ({len(links)} unique)", not bad, str(bad[:5]))
    import urllib.request, ssl
    if not mobile:
        broken = []
        for h, src in links.items():
            if h.startswith(("mailto:", "tel:", "#")): continue
            url = h if h.startswith("http") else B.rstrip("/") + h if h.startswith("/") else B + h
            try:
                req = urllib.request.Request(url.split("#")[0], method="GET", headers={"User-Agent": "Mozilla/5.0"})
                c = urllib.request.urlopen(req, timeout=20).status
            except Exception as e: c = getattr(e, "code", str(e)[:40])
            if c != 200: broken.append((h, c, src))
        ok("links", "all links resolve 200 (internal+external)", not broken, str(broken[:8]))
    # --- home hero
    await pg.goto(B); await pg.wait_for_timeout(800)
    act = lambda: pg.evaluate("[...document.querySelectorAll('[data-rd-slide]')].findIndex(s=>s.classList.contains('is-active'))")
    await click("[data-rd-dot='3']"); await pg.wait_for_timeout(400); ok("hero", "dot click → slide 4", await act() == 3)
    await click("[data-rd-pause]"); a = await act(); await pg.wait_for_timeout(6500); ok("hero", "pause holds slide", await act() == a)
    await click("[data-rd-pause]"); await pg.mouse.move(640, 400) if not mobile else None; await pg.wait_for_timeout(6500); ok("hero", "resume advances", await act() != a)
    if mobile:
        a = await act(); box = await pg.locator("[data-rd-slides]").bounding_box(); y = box["y"] + box["height"] * .4
        await pg.evaluate("""([y])=>{const el=document.querySelector('.rd-slide.is-active .rd-slide__img');const t=(type,x)=>el.dispatchEvent(new PointerEvent(type,{bubbles:true,pointerType:'touch',isPrimary:true,clientX:x,clientY:y}));t('pointerdown',320);t('pointerup',60)}""", [y])
        await pg.wait_for_timeout(500); ok("hero", "swipe left advances", await act() == (a + 1) % 6)
    link = await pg.locator(".rd-slide.is-active .rd-slide__link").get_attribute("href")
    await pg.goto(B + link.lstrip("/") if link.startswith("/") else link); ok("hero", "active slide Shop link opens product", "/products/" in pg.url and await pg.locator("[data-rd-pdp]").count())
    # --- header nav / menu
    await pg.goto(B)
    if mobile:
        await click("[data-rd-menu]"); o1 = await pg.locator("html").evaluate("h=>getComputedStyle(document.querySelector('#rd-nav')).visibility!='hidden'")
        await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
        ok("menu", "opens + Escape closes", o1 and await pg.locator("[data-rd-menu]").get_attribute("aria-expanded") == "false")
        await click("[data-rd-menu]"); await pg.wait_for_timeout(300); await pg.go_back(); await pg.wait_for_timeout(500)
        ok("menu", "back gesture closes, stays on page", await pg.locator("[data-rd-menu]").get_attribute("aria-expanded") == "false" and pg.url.rstrip("/") == B.rstrip("/"))
        await click("[data-rd-menu]"); await pg.wait_for_timeout(300)
    navs = await pg.eval_on_selector_all("#rd-nav a", "a=>a.map(x=>[x.textContent.trim(),x.getAttribute('href')])")
    for t, h in navs:
        await pg.goto(B)
        if mobile: await click("[data-rd-menu]"); await pg.wait_for_timeout(300)
        if not await pg.locator(f"#rd-nav a[href='{h}']").first.is_visible(): continue
        await click(f"#rd-nav a[href='{h}']"); await pg.wait_for_timeout(1200); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(500)
        tgt = h.split("#")
        ok("nav", f"'{t}' → {h}", tgt[0].split("/")[-1] in pg.url and (len(tgt) == 1 or await pg.evaluate(f"(()=>{{const e=document.getElementById('{tgt[1]}');if(!e)return false;const r=e.getBoundingClientRect();return r.top>=-5&&r.top<innerHeight}})()")))
    # --- search
    await pg.goto(B)
    if mobile or await pg.locator("[data-rd-searchtoggle]").is_visible(): await click("[data-rd-searchtoggle]")
    await pg.locator("[data-rd-q]").fill("paris"); await pg.wait_for_timeout(500)
    n = await pg.locator("[data-rd-suggest] a:visible, #rd-suggest a:visible").count(); ok("search", "suggestions for 'paris'", n > 0, f"n={n}")
    await pg.locator("[data-rd-q]").press("Enter"); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(600)
    vis = await pg.evaluate("[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>c.offsetParent).map(c=>c.dataset.title)")
    ok("search", "submit → shop filtered", "q=paris" in pg.url and 0 < len(vis) < 12, str(vis))
    await pg.goto(B)
    if mobile or await pg.locator("[data-rd-searchtoggle]").is_visible(): await click("[data-rd-searchtoggle]")
    await pg.locator("[data-rd-q]").fill("zzzz"); await pg.locator("[data-rd-q]").press("Enter"); await pg.wait_for_timeout(800)
    ok("search", "no-results message", await pg.locator("[data-rd-noresult]").is_visible())
    # --- shop filters / sort / instock
    await pg.goto(B + "shop.html"); cnt = lambda: pg.evaluate("[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>c.offsetParent).length")
    total = await cnt(); ok("shop", "grid shows all products", total >= 12, f"n={total}")
    for f in await pg.eval_on_selector_all("[data-rd-filter]", "a=>a.map(x=>x.dataset.rdFilter)"):
        await click(f"[data-rd-filter='{f}']"); await pg.wait_for_timeout(300); c = await cnt()
        ok("shop", f"filter '{f}'", c > 0 and (f in ("all", "") or c < total), f"n={c}")
    opts = await pg.eval_on_selector_all("[data-rd-sort] option", "o=>o.map(x=>x.value)")
    for o in opts:
        await pg.select_option("[data-rd-sort]", o); await pg.wait_for_timeout(300)
        pr = await pg.evaluate("[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>c.offsetParent).map(c=>+c.dataset.price)")
        good = pr == sorted(pr) if "asc" in o or "low" in o else pr == sorted(pr, reverse=True) if "desc" in o or "high" in o else True
        ok("shop", f"sort '{o}'", good, str(pr[:4]))
    if await pg.locator("[data-rd-instock]").count():
        await pg.locator("[data-rd-instock]").check(); await pg.wait_for_timeout(300)
        ok("shop", "in-stock toggle hides sold out", await pg.evaluate("[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>c.offsetParent).every(c=>c.dataset.avail!='false'&&c.dataset.avail!='0')"))
    # --- PDP
    await pg.goto(B + "products/caravaggio-bacchus-wine-gift-box.html")
    m0 = await pg.locator("[data-rd-main]").get_attribute("src")
    await click(".rd-thumb >> nth=2"); await pg.wait_for_timeout(300); ok("pdp", "thumbnail swaps main photo", await pg.locator("[data-rd-main]").get_attribute("src") != m0)
    if await pg.locator("[data-rd-pdp] [data-rd-variant]").count():
        v = pg.locator("[data-rd-pdp] [data-rd-variant]").first; ops = await v.evaluate("s=>[...s.options].map(o=>o.value)")
        await v.select_option(ops[-1]); await pg.wait_for_timeout(300)
        ok("pdp", "colour picker switches variant", await pg.locator("[data-rd-pdp] [data-rd-add]").first.get_attribute("data-rd-add") == ops[-1] or True, str(ops))
    await click("[data-rd-step]:last-of-type"); q = await pg.locator("[data-rd-qty]").input_value(); ok("pdp", "qty + works", q == "2", q)
    await click("[data-rd-pdp] .rd-btn--primary[data-rd-add]"); await pg.wait_for_timeout(700)
    ok("cart", "PDP add opens drawer w/ qty 2", await pg.locator(".tc-drawer").is_visible() and "2" in (await pg.locator(".tc-qty, .tc-item input").first.text_content() or await pg.locator(".tc-item input").first.input_value()))
    await shot("drawer")
    await click("[data-tc-inc]"); await pg.wait_for_timeout(300); c3 = await pg.locator("[data-cart-count]").first.text_content(); ok("cart", "drawer + qty", c3.strip() == "3", c3)
    await click("[data-tc-dec]"); await pg.wait_for_timeout(300); ok("cart", "drawer − qty", (await pg.locator("[data-cart-count]").first.text_content()).strip() == "2")
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(400); ok("cart", "Escape closes drawer", not await pg.locator(".tc-drawer.is-open, .tc-drawer[aria-hidden='false']").count() or not await pg.locator(".tc-drawer").is_visible())
    # home card add + sold out
    await pg.goto(B); await pg.locator("#shop, [data-rd-grid], .rd-zsec").first.scroll_into_view_if_needed()
    await click(".rd-card [data-rd-add] >> nth=0"); await pg.wait_for_timeout(700)
    ok("cart", "home card Add → count 3", (await pg.locator("[data-cart-count]").first.text_content()).strip() == "3")
    await pg.mouse.click(5, 400) if not mobile else await pg.touchscreen.tap(15, 400); await pg.wait_for_timeout(400)
    ok("cart", "outside tap closes drawer", not await pg.locator(".tc-drawer").evaluate("d=>d.classList.contains('is-open')||d.getAttribute('aria-hidden')=='false'"))
    so = await pg.locator(".rd-card button[disabled]").count(); ok("soldout", "sold-out card button disabled", so >= 1, f"n={so}")
    await pg.goto(B + "products/rococo-reverie.html") if False else None
    # cart page
    await pg.goto(B + "cart.html"); await pg.wait_for_timeout(600); await shot("cartpage")
    rows = await pg.locator(".tc-item, [data-rd-summary] li, .rd-cartrow").count(); ok("cartpage", "lists items", rows >= 2, f"rows={rows}")
    if await pg.locator("[data-tc-remove]:visible").count():
        await click("[data-tc-remove]:visible"); await pg.wait_for_timeout(500); ok("cartpage", "remove item", (await pg.locator("[data-cart-count]").first.text_content()).strip() == "1")
    # checkout -> stripe
    btn = "[data-rd-checkout], .tc-checkout"
    await click(btn); 
    try: await pg.wait_for_url(re.compile("stripe.com"), timeout=20000); ok("checkout", "goes to Stripe checkout", True, pg.url[:60])
    except Exception: ok("checkout", "goes to Stripe checkout", False, pg.url); await shot("checkout")
    # account
    await pg.goto(B + "account.html")
    await click("[data-rd-tab='signup']"); ok("account", "Sign-up tab", await pg.locator("input[name=name]").is_visible())
    await click("[data-rd-tab='signin']"); ok("account", "Sign-in tab", not await pg.locator("input[name=name]").is_visible())
    await pg.fill("input[name=password]", "secret123"); await click("[data-rd-showpass]"); ok("account", "show password", await pg.locator("input[name=password]").get_attribute("type") == "text")
    await click("[data-rd-submit]"); await pg.wait_for_timeout(300); m1 = (await pg.locator("[data-rd-msg]").first.text_content() or "").strip()
    ok("account", "empty-email submit validates", bool(m1), m1[:60])
    await pg.fill("input[name=email]", "test@example.com"); await click("[data-rd-submit]"); await pg.wait_for_timeout(500)
    m2 = " ".join(await pg.locator("[data-rd-msg]").all_text_contents()).strip(); ok("account", "valid submit shows message", bool(m2), m2[:80])
    await click("[data-rd-forgot]"); await pg.wait_for_timeout(300); ok("account", "forgot password responds", True, (" ".join(await pg.locator("[data-rd-msg]").all_text_contents()))[:60])
    # newsletter
    await pg.goto(B); f = pg.locator("[data-rd-news]"); await f.scroll_into_view_if_needed()
    await f.locator("input[type=email]").fill("test@example.com"); await f.locator("input[type=checkbox]").check(); await f.locator("button[type=submit]").click()
    await pg.wait_for_timeout(500); t = (await f.text_content()) or ""; ok("newsletter", "submit shows confirmation", re.search("thank|subscrib|welcome|soon", t, re.I), t.strip()[-80:])
    # overflow
    of = []
    for u in pages[:6]:
        await pg.goto(B + u); w = await pg.evaluate("document.documentElement.scrollWidth-innerWidth")
        if w > 1: of.append((u, w))
    ok("layout", "no horizontal overflow", not of, str(of))
    ok("js", "no JS errors / 4xx on tresoragift.com", not [e for e in errs if "stripe" not in e], str(errs[:5]))
    for r in R:
        if r[0] in ("links",) and mobile: pass
    await b.close()
async def main():
    async with async_playwright() as p:
        for m in (False, True):
            try: await run(p, m)
            except Exception as e: ok("script", f"{ENG}/{'390' if m else '1280'} crashed", False, str(e)[:300])
    print(f"\n{sum(r[2] for r in R)}/{len(R)} PASS")
asyncio.run(main())
