"""Full-site checks for redesign/v1..v3 (home, shop, cart, account, 12 product pages each) in Chromium and WebKit at 1280 and 390.
usage: python3 tools/redesign_check.py SITE_ROOT_URL [--shots DIR] [--only 1,2,3] [--engines chromium,webkit]"""
import asyncio, sys, json, os, re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
BASE = sys.argv[1].rstrip("/") + "/"
args = sys.argv[2:]
SHOTS = args[args.index("--shots") + 1] if "--shots" in args else None
ONLY = [int(x) if x.isdigit() else x for x in args[args.index("--only") + 1].split(",")] if "--only" in args else [1, 2, 3, 4]   # 0 = main site at the root; a name = /bg/<name>/ preview
ENGINES = args[args.index("--engines") + 1].split(",") if "--engines" in args else ["chromium", "webkit"]
s = open("assets/js/catalog.js").read(); CAT = json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])
HANDLES = sorted(p["handle"] for p in CAT["products"].values())
PAGES = ["", "shop.html", "cart.html", "account.html"] + [f"products/{h}.html" for h in HANDLES]
if SHOTS: os.makedirs(SHOTS, exist_ok=True)

async def load_all(pg):
    h = await pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, h + 900, 700):
        await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(40)
    await pg.evaluate("Promise.all([...document.images].map(i=>i.complete?0:new Promise(r=>{i.onload=i.onerror=r;setTimeout(r,8000)})))")
    await pg.evaluate("window.scrollTo(0,0)"); await pg.wait_for_timeout(150)

async def context(p, engine, mobile):
    w, h = (390, 844) if mobile else (1280, 800)
    if engine == "webkit":
        b = await p.webkit.launch()
        ctx = await b.new_context(**(p.devices["iPhone 14"] | {"viewport": {"width": w, "height": h}}) if mobile else {"viewport": {"width": w, "height": h}})
    else:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        ctx = await b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2 if mobile else 1)
    return b, ctx

async def visible(pg, sel="#shop .rd-card, [data-rd-grid] .rd-card"):
    return await pg.evaluate(f"[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>!c.hidden).length")

async def run_variant(p, engine, mobile, n):
    tag = f"{engine}/{'390' if mobile else '1280'}/" + ("root" if n == 0 else f"bg-{n}" if isinstance(n, str) else f"v{n}")
    b, ctx = await context(p, engine, mobile)
    pg = await ctx.new_page(); errs = []; bad = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("response", lambda r: bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
    sub = "" if n == 0 else f"bg/{n}/" if isinstance(n, str) else f"redesign/v{n}/"
    root = BASE + sub; prod = f"/tresora-clone/{sub}products/"
    problems, links = [], set()
    await pg.goto(root, wait_until="load"); await pg.evaluate("localStorage.clear()")
    for path in PAGES + (["success.html", "cancel.html"] if n == 0 else []):
        resp = await pg.goto(root + path, wait_until="load", timeout=60000)
        if resp.status != 200: problems.append(f"{path}: HTTP {resp.status}")
        await load_all(pg)
        r = await pg.evaluate("""()=>({broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.getAttribute('src')),
          overflow:document.documentElement.scrollWidth-innerWidth, links:[...document.querySelectorAll('a[href]')].map(a=>a.href),
          stray:[...document.querySelectorAll('a[href*="/products/"]')].map(a=>a.getAttribute('href')).filter(h=>!h.startsWith(PROD))})""".replace("PROD", repr(prod)))
        if r["broken"]: problems.append(f"{path}: broken images {r['broken']}")
        if r["overflow"] > 0: problems.append(f"{path}: horizontal overflow {r['overflow']}px")
        if r["stray"]: problems.append(f"{path}: links leave the concept {r['stray'][:3]}")
        links.update(l.split("#")[0] for l in r["links"] if l.startswith(root) or "/redesign/" in l)
        if SHOTS and engine == "chromium" and path in ("", "shop.html", "products/klimt-the-kiss-gift-box.html", "account.html"):
            nm = (path.replace("products/", "p-").replace(".html", "") or "home")
            await pg.screenshot(path=f"{SHOTS}/v{n}-{nm}-{'m' if mobile else 'd'}.png", full_page=(path == ""))
            if path == "": await pg.screenshot(path=f"{SHOTS}/v{n}-hero-{'m' if mobile else 'd'}.png")
    t = {}
    # home: filter + add to cart + drawer link stays in concept
    await pg.goto(root, wait_until="load")
    if await pg.locator(".rd-tab[data-rd-filter=city]").count():
        await pg.click(".rd-tab[data-rd-filter=city]"); t["home_city"] = await visible(pg)
        await pg.click(".rd-tab[data-rd-filter=all]")
    else: t["home_city"] = await pg.evaluate("document.querySelectorAll('.rd-card[data-cat=city]').length")
    if await pg.locator("[data-rd-slides]").count():   # v4 slideshow: autoplay, progress, swipe, hover pause
        t["slides"] = await pg.evaluate("document.querySelectorAll('[data-rd-slide]').length")
        t["slide_names"] = await pg.evaluate("[...document.querySelectorAll('[data-rd-slide] .rd-slide__city')].map(e=>e.textContent).join('|')")
        t["slide0"] = await pg.get_attribute("[data-rd-slides]", "data-rd-current")
        t["slide_imgs_ok"] = await pg.evaluate("[...document.querySelectorAll('[data-rd-slide] img')].every(i=>i.complete&&i.naturalWidth>=1000)")
        t["slide_full"] = await pg.evaluate("(()=>{const r=document.querySelector('[data-rd-slides]').getBoundingClientRect();return Math.abs(r.width-innerWidth)<2&&Math.abs(r.height-innerHeight)<2})()")
        if not mobile: await pg.mouse.move(640, 400)
        await pg.wait_for_timeout(5600); t["slide_auto"] = await pg.get_attribute("[data-rd-slides]", "data-rd-current")
        await pg.evaluate("""(()=>{const el=document.querySelector('[data-rd-slides]'),b=el.getBoundingClientRect(),y=b.top+b.height*0.4;
          const ev=(type,x)=>el.dispatchEvent(new PointerEvent(type,{bubbles:true,clientX:x,clientY:y,pointerType:'touch',isPrimary:true}));
          ev('pointerdown',b.width*0.8);ev('pointerup',b.width*0.2);})()""")
        await pg.wait_for_timeout(200); t["slide_swipe"] = await pg.get_attribute("[data-rd-slides]", "data-rd-current")
        if not mobile:
            await pg.hover(".rd-slide.is-active .rd-slide__link"); await pg.wait_for_timeout(6000); t["slide_hold"] = await pg.get_attribute("[data-rd-slides]", "data-rd-current")
            await pg.mouse.move(640, 400)
        if SHOTS and engine == "chromium": await pg.screenshot(path=f"{SHOTS}/v{n}-slide2-{'m' if mobile else 'd'}.png")
        # full autoplay cycle from a fresh load: every slide shows in order and it wraps back to the first
        await pg.reload(wait_until="load"); await pg.mouse.move(640, 400) if not mobile else None; seen = []
        for _ in range(90):
            c = await pg.get_attribute("[data-rd-slides]", "data-rd-current")
            if not seen or seen[-1] != c:
                seen.append(c)
                if SHOTS and engine == "chromium" and c in ("1", "3", "5"):
                    await pg.wait_for_timeout(2000); await pg.screenshot(path=f"{SHOTS}/v{n}-slide{c}-{'m' if mobile else 'd'}.png")
            if len(seen) > t["slides"]: break
            await pg.wait_for_timeout(500)
        n_s = t["slides"]; t["slide_cycle"] = ",".join(seen[:n_s]); t["slide_wrap"] = seen[n_s] if len(seen) > n_s else None
    btn = pg.locator(".rd-card[data-cat=city] [data-rd-add]").first
    await btn.scroll_into_view_if_needed(); await btn.click(); await pg.wait_for_timeout(500)
    t["count"] = await pg.text_content("[data-cart-count]")
    t["drawer"] = await pg.evaluate("document.documentElement.classList.contains('tc-open')")
    t["drawer_link_ok"] = await pg.evaluate(f"[...document.querySelectorAll('.tc-items a')].every(a=>a.getAttribute('href').startsWith('{prod}'))")
    await pg.keyboard.press("Escape"); await pg.wait_for_timeout(300)
    # search from a product page navigates to the shop page with results
    await pg.goto(root + "products/paris-gift-box.html", wait_until="load")
    if mobile: await pg.click("[data-rd-searchtoggle]")
    await pg.fill("[data-rd-q]", "klimt"); await pg.wait_for_timeout(250)
    t["suggest"] = await pg.evaluate("document.querySelectorAll('[data-rd-suggest] a').length")
    await pg.press("[data-rd-q]", "Enter"); await pg.wait_for_load_state("load"); await pg.wait_for_timeout(300)
    t["search_shop"] = (urlparse(pg.url).path.endswith("shop.html"), await visible(pg))
    # shop: url filter, sort, stock filter
    await pg.goto(root + "shop.html?cat=city", wait_until="load"); t["shop_city"] = await visible(pg)
    await pg.goto(root + "shop.html", wait_until="load")
    await pg.select_option("[data-rd-sort]", "price-asc")
    prices = await pg.evaluate("[...document.querySelectorAll('[data-rd-grid] .rd-card')].filter(c=>!c.hidden).map(c=>+c.dataset.price)")
    t["sorted"] = prices == sorted(prices)
    await pg.check("[data-rd-instock]"); t["instock"] = await visible(pg)
    # product page: variant pills + qty + add
    await pg.goto(root + "products/vermeer-girl-with-a-pearl-earring-gift-box.html", wait_until="load")
    await pg.click(".rd-pills label:nth-of-type(2) span"); await pg.click("[data-rd-step='1']")
    await pg.click(".rd-pdp [data-rd-add]"); await pg.wait_for_timeout(500)
    t["count_after_pdp"] = await pg.text_content("[data-cart-count]")
    t["thumbs"] = await pg.evaluate("document.querySelectorAll('[data-rd-thumb]').length")
    await pg.keyboard.press("Escape")
    # cart page
    await pg.goto(root + "cart.html", wait_until="load"); await pg.wait_for_timeout(200)
    t["cart_lines"] = await pg.evaluate("document.querySelectorAll('.rd-line').length")
    await pg.click(".rd-line:first-child [data-rd-inc]"); await pg.wait_for_timeout(150)
    t["cart_count_inc"] = await pg.text_content("[data-cart-count]")
    if SHOTS and engine == "chromium": await pg.screenshot(path=f"{SHOTS}/v{n}-cart-{'m' if mobile else 'd'}.png")
    await pg.click(".rd-line:first-child [data-rd-remove]"); await pg.wait_for_timeout(150)
    t["cart_lines_after_remove"] = await pg.evaluate("document.querySelectorAll('.rd-line').length")
    # checkout: one product left, so Checkout must hand over to its Stripe (test mode) Payment Link
    n_err = len(errs)
    try:
        async with pg.expect_navigation(url=lambda u: "stripe.com" in u, timeout=20000, wait_until="commit"):
            await pg.click("[data-rd-checkout]")
        t["checkout_host"] = pg.url.split("/")[2]
    except Exception as e: t["checkout_host"] = f"none ({str(e)[:60]})"
    del errs[n_err:]; await pg.goto(root + "cart.html", wait_until="load"); bad[:] = [b for b in bad if "stripe" not in b]
    # account page
    await pg.goto(root + "account.html?mode=signup", wait_until="load")
    t["signup_mode"] = await pg.get_attribute("[data-rd-accountpage]", "data-mode")
    await pg.fill(".rd-auth input[name=email]", "test@example.com"); await pg.fill(".rd-auth input[name=password]", "secret123")
    await pg.click("[data-rd-submit]"); t["signup_msg"] = (await pg.text_content(".rd-auth__msg"))[:30]
    await pg.click("[data-rd-tab=signin]"); t["signin_title"] = await pg.text_content("[data-rd-modal-title]")
    # every internal link resolves
    for l in sorted(links):
        r = await ctx.request.get(l)
        if r.status != 200: problems.append(f"dead link {l} -> {r.status}")
    await b.close()
    exp = {"home_city": 4, "count": "1", "drawer": True, "drawer_link_ok": True, "search_shop": (True, 1), "shop_city": 4, "sorted": True, "instock": 11,
           "count_after_pdp": "3", "cart_lines": 2, "cart_count_inc": "4", "cart_lines_after_remove": 1, "signup_mode": "signup", "signin_title": "Welcome back", "checkout_host": "buy.stripe.com"}
    for k, v in exp.items():
        if t.get(k) != v: problems.append(f"{k}: got {t.get(k)!r}, expected {v!r}")
    if "slides" in t:
        sx = {"slides": 6, "slide_cycle": "0,1,2,3,4,5", "slide_names": "Paris|Gothic Romance|Barcelona|Caravaggio|New York|Amalfi", "slide_wrap": "0", "slide0": "0", "slide_imgs_ok": True, "slide_full": True, "slide_auto": "1", "slide_swipe": "2"}
        if not mobile: sx["slide_hold"] = "2"
        for k, v in sx.items():
            if t.get(k) != v: problems.append(f"{k}: got {t.get(k)!r}, expected {v!r}")
    if t.get("suggest", 0) < 1: problems.append("no search suggestions")
    if not t.get("signup_msg", "").startswith("Looks good"): problems.append(f"signup msg {t.get('signup_msg')}")
    problems += [f"js error {e}" for e in errs if "stripe" not in e] + [f"http {x}" for x in bad]
    print(("PASS " if not problems else "FAIL ") + tag + f"  pages={len(PAGES)} links={len(links)}" + ("" if not problems else "\n   " + "\n   ".join(problems[:15])), flush=True)
    return {"tag": tag, "problems": problems, **{k: str(v) for k, v in t.items()}}

async def main():
    out = []
    async with async_playwright() as p:
        for engine in ENGINES:
            for mobile in (False, True):
                for n in ONLY: out.append(await run_variant(p, engine, mobile, n))
    json.dump(out, open("/tmp/redesign_check.json", "w"), indent=1)
    print(f"{sum(not o['problems'] for o in out)}/{len(out)} PASS")
asyncio.run(main())
