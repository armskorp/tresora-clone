"""Sanity checks for the local copy: no external requests, no JS errors, menu/drawer/carousel behaviour."""
import asyncio
from playwright.async_api import async_playwright
URL="http://127.0.0.1:8765/"
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        ext=[]; errs=[]; bad=[]
        ctx=await b.new_context(viewport={"width":1280,"height":800}); pg=await ctx.new_page()
        pg.on("request", lambda r: ext.append(r.url) if not r.url.startswith(URL) and not r.url.startswith("data:") else None)
        pg.on("response", lambda r: bad.append((r.status, r.url)) if r.status>=400 else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL,wait_until="load"); await pg.wait_for_timeout(1500)
        for y in range(0,6000,400):
            await pg.evaluate(f"document.querySelector('.page-wrapper').scrollTop={y};window.scrollTo(0,{y})"); await pg.wait_for_timeout(60)
        await pg.evaluate("document.querySelector('.page-wrapper').scrollTop=0;window.scrollTo(0,0)")
        await pg.hover(".menu-list__link >> text=Inspired By City"); await pg.wait_for_timeout(800)
        await pg.screenshot(path="screenshots/copy-desktop-menu-hover.png")
        print("desktop external requests:", ext); print("errors:", errs); print("4xx/5xx:", bad)
        await ctx.close()
        ctx=await b.new_context(viewport={"width":390,"height":844},is_mobile=True,has_touch=True); pg=await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(URL,wait_until="load"); await pg.wait_for_timeout(1000)
        await pg.click("summary.header__icon--menu"); await pg.wait_for_timeout(800)
        await pg.screenshot(path="screenshots/copy-mobile-menu-open.png")
        print("drawer open:", await pg.evaluate("document.getElementById('Details-menu-drawer-container').open"))
        print("mobile errors:", errs)
        await b.close()
asyncio.run(main())
