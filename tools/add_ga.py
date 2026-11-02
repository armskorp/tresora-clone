"""Inject GA4 (G-VKEH4T20Q7) into every live root page. Idempotent; run after any build."""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GA = "G-VKEH4T20Q7"
SNIP = f"""<!-- GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href*="buy.stripe.com"],a[href*="checkout.stripe.com"]');if(a)gtag('event','begin_checkout',{{transport_type:'beacon'}});}},true);</script>
"""
n = 0
for f in glob.glob("*.html") + glob.glob("products/*.html"):
    s = open(f, encoding="utf-8").read()
    if GA not in s and "</head>" in s:
        s = s.replace("<head>", "<head>\n" + SNIP, 1) if "<head>" in s else s.replace("</head>", SNIP + "</head>", 1)
        open(f, "w", encoding="utf-8").write(s)
    n += GA in s
print("GA4 present in", n, "root pages")
