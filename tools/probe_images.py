"""Record rendered width of each <img> (keyed by src attr) on the live site at desktop & mobile."""
import asyncio, json
from playwright.async_api import async_playwright
BLOCK=["shop.app","hcaptcha","login_with_shop","forms.shopifyapps"]
async def run(b,w,h,mobile):
    ctx=await b.new_context(viewport={"width":w,"height":h},is_mobile=mobile,has_touch=mobile,user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36")
    pg=await ctx.new_page()
    await pg.route("**/*", lambda r: r.abort() if any(k in r.request.url for k in BLOCK) else r.continue_())
    await pg.goto("https://tresora.store/",wait_until="load"); await pg.wait_for_timeout(3000)
    d=await pg.evaluate("""()=>[...document.images].map(i=>[i.getAttribute('src'),Math.round(i.getBoundingClientRect().width)])""")
    bg=await pg.evaluate("""()=>{const o=new Set();for(const e of document.querySelectorAll('*')){const b=getComputedStyle(e).backgroundImage;if(b&&b!='none'&&b.includes('url'))o.add(b)}return [...o]}""")
    await ctx.close(); return d,bg
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path="/usr/bin/google-chrome",args=["--no-sandbox"])
        D,bgd=await run(b,1280,800,False); M,bgm=await run(b,390,844,True)
        out={}
        for s,w in D+M:
            if s: out[s]=max(out.get(s,0),w)
        json.dump({"widths":out,"bg":list(set(bgd+bgm))},open("orig/img_widths.json","w"),indent=1)
        print(len(out)); print(set(bgd+bgm))
        await b.close()
asyncio.run(main())
