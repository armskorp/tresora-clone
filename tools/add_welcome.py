"""Inject the 15% welcome popup (assets/js/welcome.js) into every live root page except checkout / thank-you pages.
Idempotent. Run after any page rebuild (tools/add_ga.py calls it)."""
import glob, os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
V = "20261109a"
TAG = f'<script src="/assets/js/welcome.js?v={V}" defer></script>'
SKIP = {"success.html", "cancel.html", "cart.html", "account.html", "reset-password.html", "404.html"}
n = 0
for f in sorted(glob.glob("*.html") + glob.glob("products/*.html") + glob.glob("blog/*.html")):
    s = o = open(f, encoding="utf-8").read()
    s = re.sub(r'<script src="/assets/js/welcome\.js[^"]*"( defer)?></script>\n?', "", s)
    if os.path.basename(f) not in SKIP and "</body>" in s:
        m = re.search(r'<script src="[^"]*redesign/shared/i18n\.js', s)
        s = s[:m.start()] + TAG + s[m.start():] if m else s.replace("</body>", TAG + "\n</body>", 1)
        n += 1
    if s != o:
        open(f, "w", encoding="utf-8").write(s)
print(f"welcome popup on {n} root pages")
