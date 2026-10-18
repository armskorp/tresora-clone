"""Full-page screenshots (desktop 1280 / mobile 390) of a URL.
Handles Horizon's inner .page-wrapper scroller and scroll-reveal animations.
usage: python3 tools/capture.py URL OUT_PREFIX"""
import asyncio, sys
from playwright.async_api import async_playwright
URL, OUT = sys.argv[1], sys.argv[2]
UA_D="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
UA_M="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
BLOCK=["shop.app","hcaptcha","login_with_shop","forms.shopifyapps","shopify-forms"]
CSS="""shopify-forms-embed,shopify-chat,.chat-drawer{display:none!important}
html,body{overflow:visible!important;height:auto!important}
.page-wrapper{overflow:visible!important;height:auto!important;max-height:none!important}
*,*::before,*::after{content-visibility:visible!important;animation:none!important;transition:none!important;animation-timeline:auto!important}"""
async def shot(b, name, w, h, mobile):
    ctx = await b.new_context(viewport={"width":w,"height":h}, user_agent=UA_M if mobile else UA_D, is_mobile=mobile, has_touch=mobile)
    pg = await ctx.new_page()
    await pg.route("**/*", lambda r: r.abort() if any(k in r.request.url for k in BLOCK) else r.continue_())
    await pg.goto(URL, wait_until="load", timeout=60000); await pg.wait_for_timeout(3000)
    for y in range(0, 9000, 300):   # trigger lazy images / observers
        await pg.evaluate(f"document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop={y}); window.scrollTo(0,{y})"); await pg.wait_for_timeout(80)
    await pg.evaluate("document.querySelectorAll('.page-wrapper').forEach(e=>e.scrollTop=0); window.scrollTo(0,0)")
    await pg.add_style_tag(content=CSS)
    await pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
    await pg.wait_for_timeout(2500)
    await pg.screenshot(path=f"{OUT}-{name}.png", full_page=True)
    print(name, await pg.evaluate("document.documentElement.scrollHeight"))
    await ctx.close()
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        await shot(b, "desktop", 1280, 800, False)
        await shot(b, "mobile", 390, 844, True)
        await b.close()
asyncio.run(main())
