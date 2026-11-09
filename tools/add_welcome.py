"""Restyle the WhatsApp button and inject the 15% welcome popup (assets/js/welcome.js) into every live root page except checkout / thank-you pages.
Idempotent. Run after any page rebuild (tools/add_ga.py calls it)."""
import glob, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
V = "20261109b"
TAG = f'<script src="/assets/js/welcome.js?v={V}" defer></script>'
# WhatsApp corner button colours (site palette: charcoal #26221e, taupe #dcd4c8); number and link unchanged.
WA_STYLE = '''<style>.tr-wa{position:fixed;right:20px;bottom:24px;z-index:2147483000;width:56px;height:56px;border-radius:50%;background:#26221e;border:1px solid rgba(220,212,200,.5);display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(0,0,0,.18);transition:transform .2s ease,background .2s ease}.tr-wa:hover{transform:translateY(-2px);background:#3a342e}.tr-wa:focus-visible{outline:2px solid #26221e;outline-offset:3px}.tr-wa svg{width:28px;height:28px;fill:#dcd4c8}@media(max-width:600px){.tr-wa{right:16px;bottom:20px;width:52px;height:52px}}</style>'''
SKIP = {"success.html", "cancel.html", "cart.html", "account.html", "reset-password.html", "404.html"}
n = 0
for f in sorted(glob.glob("*.html") + glob.glob("products/*.html") + glob.glob("blog/*.html")):
    s = o = open(f, encoding="utf-8").read()
    s = re.sub(r'<style>\.tr-wa\{.*?</style>', lambda m: WA_STYLE, s, count=1)
    s = re.sub(r'<script src="/assets/js/welcome\.js[^"]*"( defer)?></script>\n?', "", s)
    if os.path.basename(f) not in SKIP and "</body>" in s:
        m = re.search(r'<script src="[^"]*redesign/shared/i18n\.js', s)
        s = s[:m.start()] + TAG + s[m.start():] if m else s.replace("</body>", TAG + "\n</body>", 1)
        n += 1
    if s != o:
        open(f, "w", encoding="utf-8").write(s)
print(f"welcome popup on {n} root pages")
