"""Check the first cards of each homepage row in iPhone emulation (WebKit or Chromium) and screenshot them.
usage: python3 tools/card_check.py URL OUT_PREFIX [webkit|chromium] [device]"""
import asyncio, sys, json
from playwright.async_api import async_playwright
URL, OUT = sys.argv[1], sys.argv[2]
ENG = sys.argv[3] if len(sys.argv) > 3 else "webkit"; DEV = sys.argv[4] if len(sys.argv) > 4 else "iPhone 14"
J = """(sec)=>{const s=document.querySelector(`[id$='${sec}']`);return [...s.querySelectorAll('product-card')].slice(0,4).map(c=>{
 const im=c.querySelector('slideshow-slide img');const r=im.getBoundingClientRect();const cs=getComputedStyle(im);
 const sl=im.closest('slideshow-slide');const scs=getComputedStyle(sl);
 const x=r.left+r.width/2,y=r.top+r.height/2;const top=(x>0&&x<innerWidth&&y>0&&y<innerHeight)?document.elementFromPoint(x,y):null;
 return {title:(c.querySelector('[class*=title] , h3')?.textContent||'').trim().slice(0,30), src:im.currentSrc.split('/').pop().slice(0,40),
  nw:im.naturalWidth, complete:im.complete, w:Math.round(r.width), h:Math.round(r.height), left:Math.round(r.left),
  op:cs.opacity, vis:cs.visibility, cv:scs.contentVisibility, trackLeft:Math.round(sl.parentElement.scrollLeft), onTop: top?(top===im||im.contains(top)):null}})}"""
async def main():
    async with async_playwright() as p:
        dev = p.devices[DEV]
        if ENG == "webkit": b = await p.webkit.launch(); ctx = await b.new_context(**dev)
        else:
            b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
            d = {k: v for k, v in dev.items() if k != "default_browser_type"}; ctx = await b.new_context(**d)
        pg = await ctx.new_page()
        await pg.goto(URL, wait_until="load", timeout=60000); await pg.wait_for_timeout(1500)
        res = {}
        for name, sec in [("art", "product_list_FbDn7g"), ("city", "product_list_WHxidn")]:
            await pg.evaluate("(sec)=>{const e=document.querySelector(`[id$='${sec}'] .section-resource-list__header`);window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 75)}", sec)
            await pg.wait_for_timeout(1200)
            res[name] = await pg.evaluate(J, sec)
            await pg.screenshot(path=f"{OUT}-{name}.png")
        print(ENG, DEV, json.dumps(res, indent=1))
        bad = [c for r in res.values() for c in r[:2] if not (c["nw"] > 0 and c["op"] == "1" and c["vis"] == "visible" and c["onTop"] is not False)]
        print("FIRST-CARD PROBLEMS:", bad or "none")
        await b.close()
asyncio.run(main())
