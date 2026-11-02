"""Own-words product copy (facts unchanged) for root product pages + Spanish. Idempotent; edits committed HTML in place."""
import os, re, glob, json, html
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
# handle -> (new EN intro, ES intro)
INTRO = {
"amalfi-gift-box": ("The Italian coast, folded into a matte black box: bright sun, bold color and an easy dolce vita mood, chosen piece by piece to be kept and loved.",
 "La costa italiana dentro de una caja negra mate: sol intenso, color vivo y el espíritu relajado de la dolce vita, elegido pieza a pieza para guardarse y disfrutarse."),
"barcelona-gift-box": ("Lift the lid and step into Park Güell — a gold clutch, a mosaic-print fan, jewel-bright stones and Gaudí’s famous lizard, gathered into one sunny evening set to unwrap slowly.",
 "Levanta la tapa y entra en el Park Güell: un clutch dorado, un abanico con estampado de mosaico, piedras de colores vivos y el famoso lagarto de Gaudí, reunidos en un set para una tarde soleada que se abre sin prisa."),
"caravaggio-bacchus-wine-gift-box": ("Rich color, a touch of gold and Caravaggio’s Bacchus framed for the wall: a cozy wine-night set for the home, curated around one of art’s most famous toasts.",
 "Color intenso, un toque de oro y el Baco de Caravaggio enmarcado para la pared: un set acogedor para noches de vino en casa, creado en torno a uno de los brindis más famosos del arte."),
"elegant-pearl-earring-table-gift-box": ("A table set after Vermeer’s Girl with a Pearl Earring — pearly light, Delft blue and soft candle glow, chosen as pieces to use and keep long after the box is open.",
 "Una mesa inspirada en La joven de la perla de Vermeer: luz nacarada, azul de Delft y el brillo suave de las velas, con piezas para usar y conservar mucho después de abrir la caja."),
"gothic-romance-decorative-glass-bottle": ("Dark elegance meets romance. Each bottle is decorated by hand with decoupage art of a pale maiden crowned in red peonies, her expression wistful, while a small skull wrapped in crimson roses rests at her heart — a quiet memento mori.",
 "La elegancia oscura se encuentra con el romanticismo. Cada botella se decora a mano con arte en decoupage de una doncella pálida coronada de peonías rojas, de mirada nostálgica, mientras una pequeña calavera envuelta en rosas carmesí descansa junto a su corazón: un discreto memento mori."),
"klimt-the-kiss-gift-box": ("Gold, rose and warm light from Klimt’s The Kiss, paired with a slow cup of tea — a romantic set made to linger on the shelf, not just to unwrap.",
 "Oro, rosa y luz cálida de El beso de Klimt, junto a una taza de té sin prisa: un set romántico hecho para quedarse, no solo para desenvolverse."),
"new-york-gift-box": ("New York in its golden age: crisp geometry, silver gleam and a Gatsby-style night on the town. The cage clutch, faceted lipstick case and dangling earrings all speak the same Art Deco language of line and light.",
 "Nueva York en su época dorada: geometría nítida, brillo plateado y una noche de ciudad al estilo Gatsby. El clutch de jaula, el estuche facetado del labial y los aretes colgantes hablan el mismo lenguaje Art Déco de líneas y luz."),
"paris-gift-box": ("Paris after dark, in black and ivory: pearls, a lace bow and a few quiet details, arranged in a black box as an evening set to open slowly.",
 "París de noche, en negro y marfil: perlas, un moño de encaje y pequeños detalles discretos, reunidos en una caja negra como un set de noche para abrir con calma."),
"rococo-reverie-decorative-glass-bottle": ("A small romantic keepsake in the spirit of the Rococo: a hand-decorated glass bottle with antique charm, gentle pastoral scenes and richly layered ornament.",
 "Un pequeño recuerdo romántico con el espíritu del Rococó: una botella de vidrio decorada a mano con encanto antiguo, delicadas escenas pastorales y ornamentos de rica textura."),
"sargent-the-wineglasses-wine-gift-box": ("After John Singer Sargent’s The Wineglasses: clear glass, candlelight, a cheese board and an unhurried evening at the table — a wine set to keep using long after the occasion.",
 "Inspirado en Las copas de vino de John Singer Sargent: cristal transparente, luz de velas, una tabla de quesos y una velada sin prisa a la mesa; un set de vino para seguir usando mucho después de la ocasión."),
"van-gogh-almond-blossom-gift-box": ("Van Gogh’s Almond Blossom in a box: soft blue, spring light, a cup of tea and a calm corner at home, chosen to be kept rather than simply opened.",
 "El Almendro en flor de Van Gogh en una caja: azul suave, luz de primavera, una taza de té y un rincón tranquilo en casa, elegido para conservarse y no solo para abrirse."),
"vermeer-girl-with-a-pearl-earring-gift-box": ("Vermeer’s Girl with a Pearl Earring at home: soft white, Delft blue, candlelight and a peaceful table — a set to live with, not just to unwrap.",
 "La joven de la perla de Vermeer en casa: blanco suave, azul de Delft, luz de velas y una mesa serena; un set para disfrutar a diario, no solo para desenvolver."),
}
PROSE = {  # old EN -> (new EN, ES)
"Personalized message card available for Mom Birthday, Women Anniversary, Housewarming, Thank You, Congratulations, or any custom occasion. Send us a message with your request, and we’ll include it in your gift box.":
 ("A personalized message card can be added for a mom’s birthday, an anniversary, a housewarming, a thank-you, congratulations or any other occasion. Message us with your wording and we’ll tuck it into the box.",
  "Podemos añadir una tarjeta con mensaje personalizado para el cumpleaños de mamá, un aniversario, una inauguración de casa, un agradecimiento, una felicitación o cualquier otra ocasión. Escríbenos con tu texto y lo incluiremos en la caja."),
"The softly aged turquoise finish is accented with warm antique-gold and bronze tones, creating the feeling of a treasured object discovered in an old European cabinet. Both sides feature dreamy vintage-style pastoral scenes, framed by elaborate scrollwork, botanical motifs, and dimensional cherub details.":
 ("Its gently aged turquoise surface is warmed by antique-gold and bronze accents, like a treasure found in an old European cabinet. Vintage-style pastoral scenes appear on both sides, surrounded by ornate scrolls, botanical motifs and raised cherub details.",
  "Su superficie turquesa suavemente envejecida se realza con acentos de oro antiguo y bronce, como un tesoro hallado en una vieja vitrina europea. Escenas pastorales de estilo vintage aparecen en ambos lados, rodeadas de volutas, motivos botánicos y querubines en relieve."),
"The intentionally weathered finish gives the bottle the character of an heirloom piece — delicate, nostalgic, and beautifully imperfect":
 ("A deliberately weathered finish gives it the feel of an heirloom: delicate, nostalgic and beautifully imperfect.",
  "Un acabado envejecido a propósito le da el aire de una reliquia familiar: delicada, nostálgica y bellamente imperfecta."),
"Each bottle is unique; minor variations in color, texture, patina, and hand-applied details are intentional and part of its artisan character":
 ("No two bottles are alike: small differences in color, texture, patina and hand-applied detail are part of the handmade character.",
  "No hay dos botellas iguales: las pequeñas diferencias de color, textura, pátina y detalles aplicados a mano forman parte de su carácter artesanal."),
"Display only. Avoid moisture, excessive handling, and direct sunlight to help preserve the artwork and decorative finish. Dust gently with a soft, dry cloth.":
 ("For display only. Keep away from moisture and direct sun, handle sparingly, and dust lightly with a soft, dry cloth to protect the artwork and finish.",
  "Solo decorativa. Mantenla lejos de la humedad y del sol directo, manipúlala lo menos posible y quita el polvo con un paño suave y seco para proteger el arte y el acabado."),
"Rococo-inspired interiors, French country decor, vintage collections, romantic dressing tables, antique-inspired shelves, European-style interiors, collectible art objects, and elegant gifts for lovers of old-world beauty.":
 ("Rococo or French-country interiors, vintage collections, a romantic vanity, antique-style shelves, European-inspired rooms, collectors of art objects, and anyone who loves old-world beauty.",
  "Interiores rococó o de estilo campestre francés, colecciones vintage, un tocador romántico, estanterías de aire antiguo, espacios de inspiración europea, coleccionistas de objetos de arte y cualquier amante de la belleza del viejo mundo."),
"Each bottle is unique; minor variations in hand-applied details are intentional and add to the artisan character":
 ("Every bottle is one of a kind; slight variations in the hand-applied details are part of its handmade character.",
  "Cada botella es única; las ligeras variaciones en los detalles aplicados a mano forman parte de su carácter artesanal."),
"Care: Display only. Avoid moisture and direct sunlight to preserve artwork. Dust gently with soft cloth.":
 ("Care: For display only. Keep away from moisture and direct sun, and dust lightly with a soft cloth.",
  "Cuidado: Solo decorativa. Mantenla lejos de la humedad y del sol directo, y quita el polvo con un paño suave."),
"Perfect for: Vintage-inspired shelving, gothic home aesthetics, dark academia decor, collectible art pieces, luxury gift":
 ("Perfect for: vintage-style shelves, gothic interiors, dark academia decor, art collectors, and a luxurious gift.",
  "Ideal para: estanterías de estilo vintage, interiores góticos, decoración dark academia, coleccionistas de arte y un regalo de lujo."),
"Questions? Email hello@tresora.store, we reply quickly.":
 ("Questions? Write to hello@tresora.store — we answer fast.", "¿Preguntas? Escríbenos a hello@tresora.store; respondemos enseguida."),
}
es = json.load(open("i18n/es.json"))
VERBATIM = True  # owner decision 2026-11-01: product copy is tresora.store body_html word for word (tools/verbatim_pdp.py); own-words rewrite disabled
if VERBATIM: raise SystemExit("rewrite_pdp_copy: disabled (VERBATIM) - product copy comes from tools/verbatim_pdp.py")
def esc(t): return t.replace("&", "&amp;")
for f in glob.glob("products/*.html"):
    h = os.path.basename(f)[:-5]; s = o = open(f).read()
    m = re.search(r'<p class="rd-pdp__intro">(.*?)</p>', s, re.S)
    if m and h in INTRO:
        new, new_es = INTRO[h]; old = html.unescape(m.group(1))
        s = s[:m.start(1)] + esc(new) + s[m.end(1):]
        tg = re.search(r'<p class="rd-pdp__tagline">(.*?)</p>', s); tag = html.unescape(tg.group(1)) if tg else ""
        meta = (tag + " " + new).strip()
        s = re.sub(r'(<meta name="description" content=")[^"]*"', lambda mm: mm.group(1) + esc(meta).replace('"', "&quot;") + '"', s, count=1)
        es[new] = new_es
        if tag and tag in es: es[meta] = es[tag] + " " + new_es
    for a, (b, b_es) in PROSE.items():
        if esc(a) in s or a in s:
            s = s.replace(esc(a), esc(b)).replace(a, esc(b)); es[b] = b_es
    if s != o: open(f, "w").write(s); print("rewrote", f)
json.dump(es, open("i18n/es.json", "w"), ensure_ascii=False, indent=0)
