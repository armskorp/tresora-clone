"""What a phone user actually sees: scroll the real page one screen at a time and stitch the viewport screenshots
(full_page screenshots don't render content-visibility:auto sections that are off screen, so they look blank).
usage: python3 tools/phone_shot.py URL OUT.png [WIDTH HEIGHT]"""
import asyncio, sys, io
from PIL import Image
from playwright.async_api import async_playwright
URL, OUT = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 390; H = int(sys.argv[4]) if len(sys.argv) > 4 else 844
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
async def main():
    async with async_playwright() as p:
        import os
        if os.environ.get("ENGINE") == "webkit":   # iPhone Safari engine
            b = await p.webkit.launch()
            ctx = await b.new_context(**p.devices["iPhone 13"] | {"viewport": {"width": W, "height": H}})
        else:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            ctx = await b.new_context(viewport={"width": W, "height": H}, is_mobile=True, has_touch=True, user_agent=UA)
        pg = await ctx.new_page()
        # block the live store's newsletter popup / Shop login / chat so the page can be compared
        await pg.route("**/*", lambda r: r.abort() if any(k in r.request.url for k in ["shop.app", "hcaptcha", "login_with_shop", "forms.shopifyapps", "shopify-forms", "shopify-chat"]) else r.continue_())
        await pg.goto(URL, wait_until="load", timeout=60000); await pg.wait_for_timeout(1500)
        tiles, y, last = [], 0, -1
        for _ in range(60):
            await pg.evaluate(f"window.scrollTo(0,{y})"); await pg.wait_for_timeout(900)
            sy = await pg.evaluate("Math.round(scrollY)")
            if sy == last: break
            tiles.append((sy, Image.open(io.BytesIO(await pg.screenshot())).convert("RGB"))); last = sy
            y = sy + H
        total = tiles[-1][0] + H
        canvas = Image.new("RGB", (W, total), "white")
        for sy, im in tiles: canvas.paste(im.resize((W, H)) if im.size != (W, H) else im, (0, sy))
        canvas.save(OUT); print(OUT, W, total, "doc height now:", await pg.evaluate("document.documentElement.scrollHeight"))
        await b.close()
asyncio.run(main())
