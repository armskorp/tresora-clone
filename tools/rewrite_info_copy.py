"""Own-words rewrite of about.html and faq.html body copy (facts unchanged) + Spanish + info_pages.json source."""
import os, json, html
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
ABOUT = [("h2","Keep This Feeling: Curated Gift Boxes & Handcrafted Treasures","Keep This Feeling: cajas de regalo curadas y tesoros hechos a mano"),
("p","A good gift carries a story. That is the idea behind every TRESORA box: each one takes its cue from a great artist, a timeless city, or a moment worth marking.","Un buen regalo lleva una historia dentro. Esa es la idea detrás de cada caja TRESORA: cada una se inspira en un gran artista, una ciudad atemporal o un momento que merece recordarse."),
("p","We build each collection to stir a feeling. Vermeer, Van Gogh, Paris, New York — every box celebrates beauty, culture and connection, pairing a framed artwork or city theme with carefully chosen pieces such as candles, chocolate and elegant accessories, so opening it feels like an occasion.","Creamos cada colección para despertar una emoción. Vermeer, Van Gogh, París, Nueva York: cada caja celebra la belleza, la cultura y la conexión, y combina una obra enmarcada o el tema de una ciudad con piezas elegidas con cuidado, como velas, chocolate y accesorios elegantes, para que abrirla sea todo un acontecimiento."),
("p","Made with intention. Our decoupage bottles and gift boxes are put together by hand in California, with care for every detail. We choose quality over quantity and aim for gifts that are kept, not forgotten.","Hecho con intención. Nuestras botellas de decoupage y cajas de regalo se preparan a mano en California, cuidando cada detalle. Preferimos la calidad a la cantidad y buscamos regalos que se conserven, no que se olviden."),
("p","A milestone, a declaration of love, or simply a wish to share something beautiful — TRESORA turns the gift into an experience: a moment held still and wrapped in art.","Un logro, una declaración de amor o simplemente el deseo de compartir algo bello: TRESORA convierte el regalo en una experiencia, un instante detenido y envuelto en arte."),
("h2","Every box is a feeling. Keep it","Cada caja es una emoción. Consérvala")]
FAQ = [("h2","What is the return policy?","¿Cuál es la política de devoluciones?"),
("p","Returns are accepted within 14 days of delivery, except for personalized gift boxes. To cancel an order, email hello@tresora.store within 12 hours of placing it.","Aceptamos devoluciones dentro de los 14 días posteriores a la entrega, excepto las cajas de regalo personalizadas. Para cancelar un pedido, escribe a hello@tresora.store en las 12 horas siguientes a realizarlo."),
("h2","Are any purchases final sale?","¿Hay compras sin devolución?"),
("p","Some items can’t be returned; they are clearly labeled as such before you buy.","Algunos artículos no admiten devolución; se indican claramente antes de la compra."),
("h2","When will I get my order?","¿Cuándo recibiré mi pedido?"),
("p","We ship as quickly as we can and email you the details as soon as your order is on its way. Delivery time depends on where you are.","Enviamos lo antes posible y te escribimos con los detalles en cuanto tu pedido sale. El plazo de entrega depende de tu ubicación."),
("h2","How much does shipping cost?","¿Cuánto cuesta el envío?"),
("p","Shipping within the US is free.","El envío dentro de EE. UU. es gratuito.")]
es = json.load(open("i18n/es.json")); info = json.load(open("i18n/info_pages.json"))
for f, items, key in (("about.html", ABOUT, "about"), ("faq.html", FAQ, "faq")):
    s = open(f).read(); i = s.find('<div class="rd-legal__body">') + len('<div class="rd-legal__body">'); j = s.find('\n<p class="rd-legal__mail">', i)
    body = "".join(f"<{t}>{html.escape(en, quote=False)}</{t}>" for t, en, _ in items)
    s = s[:i] + body + s[j:]; open(f, "w").write(s)
    for _, en, e in items: es[en] = e
    info[key] = [en for _, en, _ in items]
json.dump(es, open("i18n/es.json", "w"), ensure_ascii=False, indent=0)
json.dump(info, open("i18n/info_pages.json", "w"), ensure_ascii=False, indent=1)
