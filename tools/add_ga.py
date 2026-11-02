"""Inject GA4 + Search Console verification into every live root page. Idempotent; replaces old IDs."""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GA = "G-P2VCZH3M16"
OLD = ["G-VKEH4T20Q7"]
VERIFY = '<meta name="google-site-verification" content="ExiDnCnq1CMsfzDeBvYFI-1i98FBgaIN_-EZRvDj5qI" />'
SNIP = f"""<!-- GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href*="buy.stripe.com"],a[href*="checkout.stripe.com"]');if(a)gtag('event','begin_checkout',{{transport_type:'beacon'}});}},true);</script>
"""
n = 0
for f in sorted(glob.glob("*.html") + glob.glob("products/*.html")):
    s = o = open(f, encoding="utf-8").read()
    for old in OLD: s = s.replace(old, GA)
    if "</head>" in s:
        if GA not in s:
            s = s.replace("<head>", "<head>\n" + SNIP, 1) if "<head>" in s else s.replace("</head>", SNIP + "</head>", 1)
        if "google-site-verification" not in s:
            s = s.replace("<!-- GA4 -->", VERIFY + "\n<!-- GA4 -->", 1)
    if s != o: open(f, "w", encoding="utf-8").write(s)
    n += GA in s
print("GA4 present in", n, "root pages")
