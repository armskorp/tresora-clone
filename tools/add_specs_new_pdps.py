"""Idempotent: size/materials lines on every product page (facts from tresora.store products .json, own words),
new PDPs for Gothic Portraits Vase + Crow & Roses Bottle (no Stripe link yet: 'Coming soon', disabled),
shop grid cards, search catalog, sitemap, sizes.json and Spanish. Edits committed HTML in place."""
import os, re, json, io, urllib.request
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
es = json.load(open("i18n/es.json"))
if True: raise SystemExit("add_specs_new_pdps: one-time (already applied in c247229); product copy now comes verbatim from tools/verbatim_pdp.py")
def E(t): return t.replace("&", "&amp;").replace('"', "&quot;")
def sp(t): return f'<p class="rd-inside__spec">{E(t)}</p>'
# ---- 1. size & materials for gift boxes (only facts stated on tresora.store; overall box size is not published) ----
SPECS = {
 "amalfi-gift-box": [("Materials: woven raffia mini bag on a gold-tone chain strap · gold-tone charm necklace · keychain with pearl accents",
   "Materiales: mini bolso de rafia tejida con correa de cadena dorada · collar de dijes en tono dorado · llavero con detalles de perlas")],
 "barcelona-gift-box": [("Size: clutch 5.51 × 2.76 × 1.46 in (14 × 7 × 3.7 cm), W × H × D", "Tamaño: clutch de 14 × 7 × 3,7 cm (5,51 × 2,76 × 1,46 in), ancho × alto × fondo"),
   ("Materials: gold hard-shell clutch with chain strap · gold-tone earrings and bracelet set with multicolor cubic zirconia · metallic lipstick tube",
    "Materiales: clutch rígido dorado con correa de cadena · aretes y pulsera en tono dorado con circonitas multicolor · labial en estuche metálico")],
 "new-york-gift-box": [("Size: cage clutch approx. 4.92 × 4.72 in", "Tamaño: clutch de jaula de aprox. 4,92 × 4,72 in"),
   ("Materials: silver metal cage clutch · silver-tone earrings · rhinestone keychain", "Materiales: clutch de jaula de metal plateado · aretes en tono plateado · llavero de strass")],
 "paris-gift-box": [("Materials: pearl-beaded evening bag · lace bow clip with pearl detail · crystal earrings · pearl-and-crystal keychain",
   "Materiales: bolso de noche bordado con perlas · pasador de moño de encaje con detalle de perla · aretes de cristal · llavero de perlas y cristal")],
 "elegant-pearl-earring-table-gift-box": [("Materials: crystal candle holders · Delft-style ceramic bowls · wooden cheese board · table runner with pearl details",
   "Materiales: candelabros de cristal · cuencos de cerámica estilo Delft · tabla de quesos de madera · camino de mesa con detalles de perlas")],
 "sargent-the-wineglasses-wine-gift-box": [("Materials: glass wine glasses · wooden cheese board · almonds in a glass jar · gilded mini frame · table runner with pearl detailing",
   "Materiales: copas de vidrio · tabla de quesos de madera · almendras en frasco de vidrio · mini marco dorado · camino de mesa con detalles de perlas")],
 "van-gogh-almond-blossom-gift-box": [("Materials: glass cup · golden candle holder · table runner with pearl accents",
   "Materiales: taza de vidrio · candelabro dorado · camino de mesa con detalles de perlas")],
 "caravaggio-bacchus-wine-gift-box": [("Materials: cable-knit throw blanket · mini gold frame", "Materiales: manta de punto trenzado · mini marco dorado")],
 "vermeer-girl-with-a-pearl-earring-gift-box": [("Materials: crystal candle holders · Delft-style ceramic bowls · wooden cheese board · soft throw blanket",
   "Materiales: candelabros de cristal · cuencos de cerámica estilo Delft · tabla de quesos de madera · manta suave")],
 "klimt-the-kiss-gift-box": [("Materials: glass tea cup · golden candle holder · table runner with pearl details · mini gold frame",
   "Materiales: taza de té de vidrio · candelabro dorado · camino de mesa con detalles de perlas · mini marco dorado")],
}
for h, lines in SPECS.items():
    f = f"products/{h}.html"; s = o = open(f).read()
    for en, esv in lines:
        es[en] = esv
        if E(en) not in s: s = s.replace('<p class="rd-inside__pack">', sp(en) + '<p class="rd-inside__pack">', 1)
    if s != o: open(f, "w").write(s); print("specs", f)
# ---- 2. new product pages ----
SRC = "products/rococo-reverie-decorative-glass-bottle.html"
NEW = {
 "gothic-portraits-decorative-glass-vase": dict(pid=15421337763953, vid=67726334754929, price=5000,
  title="Gothic Portraits Handcrafted Decorative Glass Vase",
  imgs=["01_tresora-gothic-portrait-vase_lady-in-black_1200x1500_641a1dc6-a89b-4652-aa35-bd514d038e41.jpg","02_tresora-gothic-portrait-vase_parasol-girl_1200x1500_c47945dd-5db1-42e1-a856-012a3319415a.jpg","03_tresora-gothic-portrait-vase_skull-girl_1200x1500_e56a2735-d0f9-4499-a19b-d98a91a817cd.jpg","04_tresora-gothic-portrait-vase_in-hand-scale_1200x1500_39afd769-bf14-4897-84ba-271802e07ca3.jpg"],
  intro=[("Three gothic portraits share one round glass vase, each piece made by hand at TRESORA: a lady in black with her hair pinned up, a girl under a black lace parasol, and a girl holding a small skull. Rotate it and a new face comes forward.",
          "Tres retratos góticos comparten un mismo jarrón redondo de vidrio, hecho a mano por TRESORA: una dama de negro con el cabello recogido, una joven bajo una sombrilla de encaje negro y una joven que sostiene una pequeña calavera. Gíralo y aparece un nuevo rostro."),
         ("A cracked grey-and-white textured background gives it a softly aged look, and raised silver-and-black scrollwork outlines the rim, the base and the spaces between the portraits.",
          "Un fondo texturizado gris y blanco con craquelado le da un aire suavemente envejecido, y volutas en relieve plateadas y negras recorren el borde, la base y los espacios entre los retratos.")],
  glance=("Hand-decorated glass · decoupage art · approx. 7\" H", "Vidrio decorado a mano · arte en decoupage · aprox. 18 cm de alto"),
  items=[("Decoupage artwork applied by hand, with three different gothic portraits around the vase","Arte en decoupage aplicado a mano, con tres retratos góticos distintos alrededor del jarrón"),
         ("Cracked grey-and-white textured background","Fondo texturizado gris y blanco con craquelado"),
         ("Raised silver-and-black scrollwork at the rim, the base and between the portraits","Volutas en relieve plateadas y negras en el borde, la base y entre los retratos"),
         ("One decorative rose comes with it as a gift; the other flowers in the photos are styling only","Incluye una rosa decorativa de regalo; las demás flores de las fotos son solo de ambientación"),
         ("Made for artificial flowers or dried stems","Pensado para flores artificiales o tallos secos")],
  count=("5 details","5 detalles"),
  specs=[("Size: approx. 6.75–7 in (17–18 cm) tall · 4 in (10 cm) across","Tamaño: aprox. 17–18 cm (6,75–7 in) de alto · 10 cm (4 in) de diámetro"),
         ("Materials: Glass, decoupage paper, acrylic, textured relief finish","Materiales: vidrio, papel de decoupage, acrílico, acabado en relieve texturizado")],
  desc=[("p","Each vase is unique; small differences in texture and hand-applied detail are part of its handmade character.","Cada jarrón es único; las pequeñas diferencias de textura y de los detalles aplicados a mano forman parte de su carácter artesanal."),
        ("h3","Care","Cuidado"),
        ("p","Decorative use only. Keep it away from moisture and direct sun to protect the artwork, and dust lightly with a soft, dry cloth.","Solo decorativo. Mantenlo lejos de la humedad y del sol directo para proteger el arte, y quita el polvo con un paño suave y seco."),
        ("h3","Perfect For","Ideal para"),
        ("p","Gothic or Victorian-style rooms, dark academia shelves, a vanity or mantel, faux or dried bouquets, and anyone drawn to beautifully dark things.","Espacios de estilo gótico o victoriano, estanterías dark academia, un tocador o una repisa, ramos artificiales o secos, y cualquiera que ame la belleza oscura."),
        ("p","Free standard US shipping. Ships from Glendale, California, within 1–4 business days.","Envío estándar gratis en EE. UU. Se envía desde Glendale, California, en 1 a 4 días hábiles.")]),
 "crow-roses-decorative-bottle": dict(pid=15421127196785, vid=67725560053873, price=4000,
  title="Crow & Roses Handcrafted Decorative Glass Bottle",
  imgs=["01_tresora-gothic-crow-bottle_front-rose-light_1200x1500_e29f3827-bcc0-477e-a6bc-1f8a3f7f9d92.jpg","02_tresora-gothic-crow-bottle_front-crystal-light_1200x1500_6a4a9deb-5671-4015-ada7-21bf4b89873f.jpg","03_tresora-gothic-crow-bottle_back-rose-light_1200x1500_290bffea-bf5e-468b-8ad5-0b6ea271d24b.jpg","04_tresora-gothic-crow-bottle_in-hand-scale_1200x1500_5cb40d27-bae0-4736-9da9-c2caf1745d03.jpg"],
  intro=[("A small, darkly romantic piece for a shelf. This flat, flask-shaped glass bottle is decorated by hand at TRESORA with a doll-like gothic girl, a crow inside an ornate silver frame and deep red roses, all wrapped in a heavy silver-and-black relief that shines like old wrought iron.",
          "Una pieza pequeña y de romanticismo oscuro para tu estantería. Esta botella de vidrio plana, en forma de petaca, está decorada a mano por TRESORA con una joven gótica de aire de muñeca, un cuervo dentro de un marco plateado ornamentado y rosas rojo intenso, todo rodeado de un pesado relieve plateado y negro que brilla como hierro forjado antiguo."),
         ("The back carries on the story: sculpted roses and a tiny skull surround a panel of vintage-style script paper, a gentle memento mori.",
          "La parte trasera continúa la historia: rosas esculpidas y una diminuta calavera rodean un panel de papel con caligrafía de estilo antiguo, un sutil memento mori.")],
  glance=("Hand-decorated glass · decoupage art · 4.75\" H", "Vidrio decorado a mano · arte en decoupage · 12 cm de alto"),
  items=[("Decoupage artwork applied by hand: a gothic girl, a framed crow and red roses","Arte en decoupage aplicado a mano: una joven gótica, un cuervo enmarcado y rosas rojas"),
         ("Heavy silver-and-black textured relief border with raised detail","Borde en relieve texturizado plateado y negro, con detalles en volumen"),
         ("Back panel of vintage script paper framed by relief roses and a small skull","Panel trasero de papel con caligrafía antigua, enmarcado por rosas en relieve y una pequeña calavera"),
         ("Crystal-ball stopper included; the rose in the photos is for styling and not included","Incluye tapón de bola de cristal; la rosa de las fotos es de ambientación y no se incluye"),
         ("The bottle is not sealed and opens, so it can hold a single stem, dried flowers or small keepsakes","La botella no está sellada y se abre, así que puede contener un tallo, flores secas o pequeños recuerdos"),
         ("Decorative use only — not for food or drink","Solo decorativa: no apta para alimentos ni bebidas")],
  count=("6 details","6 detalles"),
  specs=[("Dimensions: 4.75\" H × 3.63\" W × 1.44\" D","Dimensiones: 12 cm alto × 9,2 cm ancho × 3,7 cm fondo (4,75 × 3,63 × 1,44 in)"),
         ("Materials: Glass, decoupage paper, textured relief finish, paint, crystal-ball stopper","Materiales: vidrio, papel de decoupage, acabado en relieve texturizado, pintura, tapón de bola de cristal")],
  desc=[("p","No two bottles are the same; slight differences in texture and hand-applied detail are intentional and part of its handmade character.","No hay dos botellas iguales; las ligeras diferencias de textura y de los detalles aplicados a mano son intencionales y forman parte de su carácter artesanal."),
        ("h3","Care","Cuidado"),
        ("p","For display only. Keep away from moisture and direct sun to protect the artwork, and dust lightly with a soft, dry cloth.","Solo decorativa. Mantenla lejos de la humedad y del sol directo para proteger el arte, y quita el polvo con un paño suave y seco."),
        ("h3","Perfect For","Ideal para"),
        ("p","Gothic interiors, dark academia shelves, vanity or bookshelf styling, collectors of art objects, and a thoughtful gift for anyone who loves the beautifully dark.","Interiores góticos, estanterías dark academia, decoración de tocador o librero, coleccionistas de objetos de arte y un regalo especial para quien ama la belleza oscura."),
        ("p","Free standard US shipping. Ships from Glendale, California, within 1–4 business days.","Envío estándar gratis en EE. UU. Se envía desde Glendale, California, en 1 a 4 días hábiles.")]),
}
PACK = ("Arrives in a gift pouch and box.", "Llega en una bolsita de regalo y una caja.")
CS = ("Coming soon", "Próximamente")
SOON = ("Online ordering for this piece opens soon. Questions? Write to hello@tresora.store.", "Los pedidos en línea de esta pieza abrirán pronto. ¿Preguntas? Escríbenos a hello@tresora.store.")
es[PACK[0]] = PACK[1]; es[CS[0]] = CS[1]; es[SOON[0]] = SOON[1]
CDN = "https://cdn.shopify.com/s/files/1/0701/9246/3985/files/"
sizes = json.load(open("redesign/shared/products/sizes.json"))
tpl = open(SRC).read()
from PIL import Image
for h, d in NEW.items():
    T = d["title"]; es.setdefault(T, T)
    for i, fn in enumerate(d["imgs"]):
        out = f"redesign/shared/products/{h}-{i}.jpg"
        if not os.path.exists(out):
            im = Image.open(io.BytesIO(urllib.request.urlopen(CDN + fn).read())).convert("RGB")
            big = im.resize((960, 1200), Image.LANCZOS); big.save(out, quality=84, optimize=True, progressive=True)
            im.resize((192, 240), Image.LANCZOS).save(out[:-4] + "-t.jpg", quality=80, optimize=True)
            sizes[f"{h}-{i}"] = [im.width, im.height, 960, 1200]
    s = tpl
    s = re.sub(r"<title>.*?</title>", f"<title>{E(T)} · TRESORA</title>", s, count=1)
    s = re.sub(r'(<meta name="description" content=")[^"]*"', lambda m: m.group(1) + E(d["intro"][0][0]) + '"', s, count=1)
    s = re.sub(r'<span aria-current="page">.*?</span>', f'<span aria-current="page">{E(T)}</span>', s, count=1)
    s = s.replace('<span class="rd-badge">Sold out</span>', f'<span class="rd-badge">{CS[0]}</span>')
    thumbs = "".join(f'<button type="button" class="rd-thumb" data-rd-thumb="/redesign/shared/products/{h}-{i}.jpg" aria-label="Show image {i+1}"{" aria-current=\"true\"" if i==0 else ""}><img src="/redesign/shared/products/{h}-{i}-t.jpg" alt="" width="120" height="150" loading="lazy"></button>' for i in range(len(d["imgs"])))
    s = re.sub(r'<div class="rd-pdp__main">.*?</div>\s*<div class="rd-thumbs"[^>]*>.*?</div>',
        f'<div class="rd-pdp__main"><span class="rd-badge">{CS[0]}</span><img src="/redesign/shared/products/{h}-0.jpg" alt="{E(T)}" width="960" height="1200" fetchpriority="high" data-rd-img data-rd-main></div>\n    <div class="rd-thumbs" role="group" aria-label="Product images">{thumbs}</div>', s, count=1, flags=re.S)
    s = re.sub(r"<h1>.*?</h1>", f"<h1>{E(T)}</h1>", s, count=1)
    s = re.sub(r"<span data-rd-price>[^<]*</span>", f"<span data-rd-price>${d['price']/100:.2f}</span>", s, count=1)
    s = re.sub(r'(?:<p class="rd-pdp__intro">.*?</p>)+', "".join(f'<p class="rd-pdp__intro">{E(a)}</p>' for a, _ in d["intro"]), s, count=1, flags=re.S)
    s = re.sub(r'(<p class="rd-pdp__glance"><span>The piece</span> ).*?( <a href="#inside">)', lambda m: m.group(1) + E(d["glance"][0]) + m.group(2), s, count=1)
    s = re.sub(r'<button class="rd-btn rd-btn--primary rd-btn--full" type="button" disabled>Sold out</button></div>',
        f'<button class="rd-btn rd-btn--primary rd-btn--full" type="button" disabled aria-disabled="true">{CS[0]}</button></div><p class="rd-pdp__note">{E(SOON[0])}</p>', s, count=1)
    s = re.sub(r'<p class="rd-inside__count">.*?</p>', f'<p class="rd-inside__count">{d["count"][0]}</p>', s, count=1)
    s = re.sub(r"(<div class=\"rd-inside\" id=\"inside\">.*?<ol>).*?(</ol>).*?(<p class=\"rd-inside__pack\"><svg.*?</svg> ).*?(</p></div>)",
        lambda m: m.group(1) + "".join(f"<li>{E(a)}</li>" for a, _ in d["items"]) + m.group(2) + "".join(sp(a) for a, _ in d["specs"]) + m.group(3) + PACK[0] + m.group(4), s, count=1, flags=re.S)
    s = re.sub(r'<div class="rd-pdp__desc">.*?</div>', '<div class="rd-pdp__desc">' + "".join(f"<{t}>{E(a)}</{t}>" for t, a, _ in d["desc"]) + "</div>", s, count=1, flags=re.S)
    # related: drop a card pointing at itself (none yet) - template's related grid is reused as-is
    open(f"products/{h}.html", "w").write(s); print("page", h)
    for a, b in d["intro"] + d["items"] + d["specs"] + [d["glance"], d["count"]]: es[a] = b
    for _, a, b in d["desc"]: es[a] = b
    es[d["intro"][0][0]] = d["intro"][0][1]
json.dump(sizes, open("redesign/shared/products/sizes.json", "w"))
# ---- 3. shop grid cards ----
sh = open("shop.html").read()
m = re.search(r'<article class="rd-card"[^>]*data-title="handcrafted artisan glass bottle – rococo[^>]*>.*?</article>', sh, re.S)
card_t = m.group(0); last = max(int(x) for x in re.findall(r'data-order="(\d+)"', sh))
ins = ""
for n, (h, d) in enumerate(NEW.items()):
    if f'/products/{h}.html' in sh: continue
    c = card_t.replace("rococo-reverie-decorative-glass-bottle", h)
    c = re.sub(r'data-title="[^"]*"', f'data-title="{E(d["title"].lower())}"', c)
    c = re.sub(r'data-price="\d+"', f'data-price="{d["price"]}"', c); c = re.sub(r'data-order="\d+"', f'data-order="{last+1+n}"', c)
    c = c.replace("Handcrafted Artisan Glass Bottle – Rococo Reverie Collection", E(d["title"]))
    c = c.replace('width="1200" height="900"', 'width="960" height="1200"').replace("Sold out", CS[0])
    c = re.sub(r'<p class="rd-card__inside">.*?</p>', f'<p class="rd-card__inside">{E(d["glance"][0])}</p>', c)
    c = re.sub(r"<span data-rd-price>[^<]*</span>", f"<span data-rd-price>${d['price']/100:.2f}</span>", c)
    ins += "\n" + c
if ins: sh = sh.replace(card_t, card_t + ins, 1); open("shop.html", "w").write(sh); print("shop cards")
# ---- 4. search catalog (available: false -> cannot be added to cart) ----
cj = open("assets/js/catalog.js").read(); a, b = cj.find("{"), cj.rfind("}") + 1; cat = json.loads(cj[a:b])
for h, d in NEW.items():
    cat["products"][str(d["pid"])] = {"id": d["pid"], "handle": h, "title": d["title"], "image": f"redesign/shared/products/{h}-0.jpg", "variants": [d["vid"]]}
    cat["variants"][str(d["vid"])] = {"id": d["vid"], "product_id": d["pid"], "handle": h, "title": d["title"], "variant_title": "", "price": d["price"], "available": False,
        "thumb": f"redesign/shared/products/{h}-0-t.jpg", "image": f"redesign/shared/products/{h}-0.jpg"}
open("assets/js/catalog.js", "w").write(cj[:a] + json.dumps(cat, ensure_ascii=False, indent=1) + cj[b:])
# ---- 5. sitemap ----
sm = open("sitemap.xml").read()
for h in NEW:
    u = f"  <url><loc>https://tresoragift.com/products/{h}.html</loc></url>\n"
    if u.strip() not in sm: sm = sm.replace("</urlset>", u + "</urlset>")
open("sitemap.xml", "w").write(sm)
json.dump(es, open("i18n/es.json", "w"), ensure_ascii=False, indent=0)
