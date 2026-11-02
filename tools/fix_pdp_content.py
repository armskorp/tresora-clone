"""Idempotent in-place fixes to committed root HTML (build scripts don't reproduce live pages).
Product content parity with tresora.store, copy fixes, related-grid fill, footer 'Main store' label, CSS cache bump."""
import os, re, glob, json
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
NOTE = "Chocolate and card inscription may vary at TRESORA’s discretion."
ELEGANT_CARD = "Personalized message card available for Mom Birthday, Women Anniversary, Housewarming, Thank You, Congratulations, or any custom occasion. Send us a message with your request, and we’ll include it in your gift box."
COPY = {
 "sunshine, color, and la dolce vita — not a tourist souvenir pile.": "sunshine, color, and la dolce vita — gathered with care, made to be treasured.",
 "one language of lines and light, not a random souvenir pile.": "one language of lines and light, composed as a single, considered set.",
 "Not a souvenir pile — an evening set meant to be opened slowly.": "Thoughtfully composed — an evening set meant to be opened slowly.",
 "in a ornate gold case": "in an ornate gold case",
}
VER_OLD, VER_NEW = "v=20261101g", "v=20261101h"
shop = open("shop.html").read()
CARDS = {}
for m in re.finditer(r'<article class="rd-card".*?</article>', shop, re.S):
    h = re.search(r'href="/products/([a-z0-9-]+)\.html"', m.group(0)).group(1); CARDS[h] = m.group(0)
ORDER = list(CARDS)
for f in glob.glob("*.html") + glob.glob("products/*.html"):
    s = o = open(f).read()
    s = s.replace(VER_OLD, VER_NEW)
    s = s.replace('aria-label="Shopify store" title="Shopify store"', 'aria-label="Main store" title="Main store"')
    for a, b in COPY.items(): s = s.replace(a, b)
    if f.startswith("products/"):
        h = os.path.basename(f)[:-5]
        if NOTE not in s:
            s = re.sub(r'(<div class="rd-pdp__desc">.*?)(</div>)', lambda m: m.group(1) + f'<p class="rd-pdp__note">{NOTE}</p>' + m.group(2), s, count=1, flags=re.S)
        if h == "elegant-pearl-earring-table-gift-box" and ELEGANT_CARD not in s:
            s = s.replace('<div class="rd-pdp__desc">', f'<div class="rd-pdp__desc"><h3>Message Card</h3><p>{ELEGANT_CARD}</p>', 1)
        if h == "amalfi-gift-box":  # drop the "Add Any Name or Message" image: no personalization field on this site
            s = re.sub(r'<button type="button" class="rd-thumb" data-rd-thumb="/redesign/shared/products/amalfi-gift-box-10\.jpg".*?</button>', '', s, flags=re.S)
        # related: fill to 4 cards (same category first, then others in shop order)
        m = re.search(r'(<div class="rd-grid rd-grid--related">)(.*?)(</div></section></main>)', s, re.S)
        if m:
            have = re.findall(r'<article class="rd-card".*?</article>', m.group(2), re.S)
            hs = [re.search(r'href="/products/([a-z0-9-]+)\.html"', a).group(1) for a in have]
            if len(have) < 4:
                extra = [x for x in ORDER if x != h and x not in hs][:4 - len(have)]
                body = m.group(2) + "".join(CARDS[x] for x in extra)
                s = s[:m.start()] + m.group(1) + body + m.group(3) + s[m.end():]
                s = re.sub(r'(<section class="rd-section rd-related">.*?<h2>)More from [^<]*(</h2>)', r'\1More to discover\2', s, count=1, flags=re.S)
    if s != o: open(f, "w").write(s); print("patched", f)
# Spanish
es = json.load(open("i18n/es.json")); add = {
 NOTE: "El chocolate y la inscripción de la tarjeta pueden variar a criterio de TRESORA.",
 "Message Card": "Tarjeta con mensaje",
 ELEGANT_CARD: "Tarjeta con mensaje personalizado disponible para cumpleaños de mamá, aniversario, inauguración de casa, agradecimiento, felicitaciones o cualquier ocasión. Envíanos un mensaje con tu solicitud y la incluiremos en tu caja de regalo.",
 "More to discover": "Más por descubrir", "Main store": "Tienda principal"}
ESCOPY = {"no un montón de recuerdos turísticos.": "reunidos con cuidado para atesorarse.",
 "un solo lenguaje de líneas y luz, no un montón de recuerdos al azar.": "un solo lenguaje de líneas y luz, compuesto como un set único y pensado.",
 "No es un montón de recuerdos: es un set de noche": "Compuesto con esmero: un set de noche"}
new = {}
for k, v in es.items():
    k2 = k
    for a, b in COPY.items(): k2 = k2.replace(a, b)
    for a, b in ESCOPY.items(): v = v.replace(a, b)
    new[k2] = v
new.update(add); json.dump(new, open("i18n/es.json", "w"), ensure_ascii=False, indent=0)
