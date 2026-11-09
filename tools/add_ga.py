"""Inject GTM + GA4 + Search Console verification into every live root page. Idempotent; replaces old IDs."""
import glob, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GA = "G-P2VCZH3M16"
GTM = "GTM-WPWBTDDN"
OLD = ["G-VKEH4T20Q7"]
VERIFY = '<meta name="google-site-verification" content="ExiDnCnq1CMsfzDeBvYFI-1i98FBgaIN_-EZRvDj5qI" />'
# Owner's exact GTM head snippet (container GTM-WPWBTDDN), placed as high in <head> as possible.
GTM_SNIP = f"""<!-- GTM -->
<script async src="https://www.googletagmanager.com/gtm.js?id={GTM}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
</script>
"""
SNIP = f"""<!-- GA4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');
document.addEventListener('click',function(e){{var a=e.target.closest&&e.target.closest('a[href*="buy.stripe.com"],a[href*="checkout.stripe.com"]');if(a)gtag('event','begin_checkout',{{transport_type:'beacon'}});}},true);</script>
"""

def insert_after_head(s, block):
    if "<head>" in s:
        return s.replace("<head>", "<head>\n" + block, 1)
    return s.replace("</head>", block + "</head>", 1)

n_ga = n_gtm = 0
for f in sorted(glob.glob("*.html") + glob.glob("products/*.html") + glob.glob("blog/*.html")):
    s = o = open(f, encoding="utf-8").read()
    for old in OLD:
        s = s.replace(old, GA)
    if "</head>" in s:
        if GTM not in s:
            s = insert_after_head(s, GTM_SNIP)
        if GA not in s:
            # Keep GA after GTM when both are being added; otherwise after <head>.
            if "<!-- GTM -->" in s and "<!-- GA4 -->" not in s:
                # Insert GA immediately after the GTM block (two </script> tags after the marker).
                marker = "<!-- GTM -->"
                idx = s.find(marker)
                end = idx
                for _ in range(2):
                    end = s.find("</script>", end)
                    if end < 0:
                        end = -1
                        break
                    end += len("</script>")
                if end > idx:
                    if end < len(s) and s[end] == "\n":
                        end += 1
                    s = s[:end] + SNIP + s[end:]
                else:
                    s = insert_after_head(s, SNIP)
            else:
                s = insert_after_head(s, SNIP)
        if "google-site-verification" not in s:
            if "<!-- GTM -->" in s:
                s = s.replace("<!-- GTM -->", VERIFY + "\n<!-- GTM -->", 1)
            elif "<!-- GA4 -->" in s:
                s = s.replace("<!-- GA4 -->", VERIFY + "\n<!-- GA4 -->", 1)
            else:
                s = insert_after_head(s, VERIFY + "\n")
    if s != o:
        open(f, "w", encoding="utf-8").write(s)
    n_ga += GA in s
    n_gtm += GTM in s
print(f"GA4 present in {n_ga} root pages; GTM {GTM} present in {n_gtm} root pages")

import subprocess as _sp, sys as _sy
_sp.run([_sy.executable, "tools/add_welcome.py"], check=True)
