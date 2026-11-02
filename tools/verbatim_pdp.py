"""Owner decision (2026-11-01): product description text is tresora.store body_html, word for word (this site replaces it;
product canonicals via tools/canonical_src.py). Idempotent; rewrites intro/tagline, 'inside' list, spec/pack lines and
description blocks of products/*.html from https://tresora.store/products.json. Our own Materials lines stay only on
pages whose source has no Materials text; the discretion note stays on gift boxes (fix_pdp_content.py).
  python3 tools/verbatim_pdp.py          apply
  python3 tools/verbatim_pdp.py --check  report pages whose text differs from the source (exit 1 on mismatch)
  python3 tools/verbatim_pdp.py --missing-es  list copied strings with no Spanish in i18n/es.json"""
import os, re, sys, json, html, urllib.request
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
SRC = json.load(urllib.request.urlopen(urllib.request.Request("https://tresora.store/products.json?limit=250", headers={"User-Agent": "Mozilla/5.0"})))["products"]
def norm(t): return re.sub(r"\s+", " ", html.unescape(t).replace("\xa0", " ")).strip()
def blocks(body):
    """[(text, label)]: one per <p>/<li>/<br>-line; label = <strong>...</strong> lead-in (e.g. 'Care:'), 'li' for list items."""
    x = re.sub(r"<li\b[^>]*>", "\n\x01", body)
    x = re.sub(r"<strong>(.*?)</strong>", lambda m: "\x02" + re.sub(r"<[^>]+>", "", m.group(1)) + "\x03", x, flags=re.S)
    x = re.sub(r"<br\s*/?>|</?(?:p|li|div|ul|ol)\b[^>]*>", "\n", x)
    lines = [norm(re.sub(r"<[^>]+>", " ", l)) for l in x.split("\n")]
    lines = [l for l in lines if l.replace("\x01", "").strip()]
    out, i = [], 0
    while i < len(lines):
        l = lines[i]; i += 1
        if l.startswith("\x01"): out.append((l[1:].strip(), "li")); continue
        m = re.match(r"\x02(.*?)\x03\s*(.*)$", l)
        if m:
            lab, t = norm(m.group(1)), m.group(2).strip()
            if not t and i < len(lines) and not lines[i].startswith(("\x01", "\x02")): t = lines[i]; i += 1
            out.append((t, lab)); continue
        out.append((l.replace("\x02", "").replace("\x03", ""), ""))
    return out
def split(p):
    b = blocks(p["body_html"]); T = norm(p["title"])
    hi = next(i for i, (t, l) in enumerate(b) if (l if l and l != "li" else t).upper().startswith(("WHAT’S INSIDE", "WHAT'S INSIDE", "DETAILS")))
    intro = [t for t, l in b[:hi] if t and t != T]
    items, specs, j = [], [], hi + 1
    while j < len(b):
        t, l = b[j]
        if l == "li" or t.startswith("✨") and l == "": items.append(t.lstrip("✨").strip())
        elif re.match(r"(Size|Dimensions|Materials):", t) and not l: specs.append(t)
        else: break
        j += 1
    rest = b[j:]
    return intro, items, specs, rest
SPEC = re.compile(r"^(Size|Dimensions|Materials):?$")
def E(t): return html.escape(t, quote=False)
def render(h, p, s):
    intro, items, specs, rest = split(p)
    pack = items.pop() if items and re.search(r"gift box.*ready to give", items[-1], re.I) else None
    desc, spec_html, pack_txt = [], [sp for sp in specs], pack
    for t, l in rest:
        if l and SPEC.match(l): spec_html.append(f"{l} {t}"); continue
        if l and "PACKAGING" in l.upper(): pack_txt = None; desc.append(("h3", l)); desc.append(("p", t)); continue
        if l and l != "li": desc.append(("h3", l)); t and desc.append(("p", t)); continue
        if t.isupper() and len(t) < 40: desc.append(("h3", t)); continue
        desc.append(("p", t))
    has_mat = any(x.startswith("Materials") for x in spec_html)
    # keep our own Materials line only where the source has none
    own = re.findall(r'<p class="rd-inside__spec">(Materials:[^<]*)</p>', s)
    if not has_mat: spec_html += [html.unescape(o) for o in own]
    # tagline + intro
    first, more = (intro[0], intro[1:]) if intro else ("", [])
    if '<p class="rd-pdp__tagline">' in s: s = re.sub(r'<p class="rd-pdp__tagline">.*?</p>', f'<p class="rd-pdp__tagline">{E(first)}</p>', s, count=1); ip = more
    else: ip = intro
    s = re.sub(r'(?:<p class="rd-pdp__intro">.*?</p>\s*)+', "".join(f'<p class="rd-pdp__intro">{E(x)}</p>' for x in ip) + "\n    ", s, count=1, flags=re.S)
    s = re.sub(r'(<meta name="description" content=")[^"]*"', lambda m: m.group(1) + html.escape(" ".join(intro)[:300]) + '"', s, count=1)
    # inside list, specs, pack
    m = re.search(r'(<div class="rd-inside" id="inside">.*?<ol>).*?(</ol>)(.*?)(</div>)', s, re.S)
    tail = "".join(f'<p class="rd-inside__spec">{E(x)}</p>' for x in spec_html)
    pk = re.search(r'(<p class="rd-inside__pack"><svg.*?</svg> ).*?</p>', m.group(3), re.S)
    if pk and pack_txt: tail += pk.group(1) + E(pack_txt) + "</p>"
    s = s[:m.start()] + m.group(1) + "".join(f"<li>{E(x)}</li>" for x in items) + m.group(2) + tail + m.group(4) + s[m.end():]
    s = re.sub(r'(<p class="rd-inside__count">)(\d+)( [^<]*</p>)', lambda mm: mm.group(1) + str(len(items)) + mm.group(3), s, count=1)
    # description blocks (+ keep discretion note if present)
    note = re.search(r'<p class="rd-pdp__note">[^<]*</p>', s.split('<div class="rd-pdp__desc">', 1)[1].split("</div>", 1)[0])
    s = re.sub(r'<div class="rd-pdp__desc">.*?</div>', lambda _: '<div class="rd-pdp__desc">' + "".join(f"<{t}>{E(x)}</{t}>" for t, x in desc) + (note.group(0) if note else "") + "</div>", s, count=1, flags=re.S)
    return s, intro + items + spec_html + ([pack_txt] if pack_txt else []) + [x for _, x in desc]
def visible(s):
    a = s.find('<div class="rd-pdp__info">'); b = s.find('<section class="rd-section rd-related">')
    return norm(re.sub(r"<[^>]+>", " ", s[a:b]))
es = json.load(open("i18n/es.json")); bad = 0; miss = set()
for p in SRC:
    h = p["handle"]; f = f"products/{h}.html"
    if not os.path.exists(f): print("NO PAGE", h); bad += 1; continue
    s0 = open(f).read(); s, strings = render(h, p, s0)
    if "--check" in sys.argv:
        intro, items, specs, rest = split(p); v = visible(s0)
        need = intro + items + specs + [t for t, l in rest if t] + [l for t, l in rest if l and l != "li"]
        lost = [x for x in need if E(x) not in v and x not in v and x not in html.unescape(v)]
        print("MATCH" if not lost else "DIFF ", h, "" if not lost else lost[:3]); bad += bool(lost); continue
    miss |= {x for x in strings if x and x not in es}
    if "--missing-es" in sys.argv: continue
    if s != s0: open(f, "w").write(s); print("verbatim", f)
if "--missing-es" in sys.argv: json.dump(sorted(miss), open("/tmp/missing_es.json", "w"), ensure_ascii=False, indent=0); print(len(miss), "missing -> /tmp/missing_es.json")
sys.exit(1 if bad else 0)
