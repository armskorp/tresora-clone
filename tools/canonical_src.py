"""OPTIONAL product-page canonicals -> tresora.store. OFF by default; nothing is added unless --enable is passed.
  python3 tools/canonical_src.py            (default, OFF) strip every data-src-canonical tag from products/*.html
  python3 tools/canonical_src.py --enable   add <link rel="canonical" href="https://tresora.store/products/<handle>" data-src-canonical>
                                            to product pages only, for handles in tresora.store/products.json whose URL returns 200
Removal before the site migration = run it without flags. Idempotent; other pages are never touched."""
import os, re, sys, glob, json, urllib.request
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
PAT = re.compile(r'<link rel="canonical" href="[^"]*" data-src-canonical>\n?')
UA = {"User-Agent": "Mozilla/5.0"}
enable = "--enable" in sys.argv
handles = {p["handle"] for p in json.load(urllib.request.urlopen(urllib.request.Request("https://tresora.store/products.json?limit=250", headers=UA)))["products"]} if enable else set()
for f in sorted(glob.glob("products/*.html")):
    h = os.path.basename(f)[:-5]; s0 = open(f).read(); s = PAT.sub("", s0)
    if enable and h in handles:
        url = f"https://tresora.store/products/{h}"
        if urllib.request.urlopen(urllib.request.Request(url, headers=UA)).status == 200:
            s = s.replace("</head>", f'<link rel="canonical" href="{url}" data-src-canonical>\n</head>', 1)
    if s != s0: open(f, "w").write(s); print("updated", f)
