/* TRESORA SEO pass — idempotent. Adds canonical (tresoragift.com), Open Graph / Twitter tags, JSON-LD
   (Organization + WebSite on home, Product + BreadcrumbList on product pages), noindex on utility pages,
   SEO titles / meta descriptions, alt text on gallery thumbnails, and rebuilds sitemap.xml.
   Node:    node tools/seo_pass.js            (run from the repo root, after the build scripts)
   Browser: seoTransform(path, html) / seoSitemap(paths, date) are pure functions. */
(function (root) {
  var SITE = "https://tresoragift.com";
  var DEFAULT_IMG = "/redesign/shared/img/slide-paris.jpg";
  var NOINDEX = ["account.html", "cart.html", "cancel.html", "success.html", "reset-password.html"];
  var SAME_AS = ["https://www.instagram.com/tresora.gift/", "https://www.tiktok.com/@tresorastore",
    "https://www.facebook.com/TRESORAgifts", "https://www.pinterest.com/TRESORAgift/", "https://www.etsy.com/shop/TRESORAgift"];
  var TITLES = {
    "index.html": "Art & City Gift Boxes for Her · Unique Gifts · TRESORA",
    "shop.html": "Shop Unique Gift Boxes for Women · Free US Shipping · TRESORA",
    "products/amalfi-gift-box.html": "Amalfi Gift Box · Italian Summer Gift Set for Her · TRESORA",
    "products/barcelona-gift-box.html": "Barcelona Gift Box · Spanish-Inspired Gift Set for Her · TRESORA",
    "products/caravaggio-bacchus-wine-gift-box.html": "Caravaggio Bacchus Wine Gift Box · Gift for Wine Lovers · TRESORA",
    "products/crow-roses-decorative-bottle.html": "Crow & Roses Hand-Decorated Glass Bottle · Gothic Decor · TRESORA",
    "products/elegant-pearl-earring-table-gift-box.html": "Elegant Girl Pearl Earring Gift Box for Her · TRESORA",
    "products/gothic-portraits-decorative-glass-vase.html": "Gothic Portraits Hand-Decorated Glass Vase · TRESORA",
    "products/gothic-romance-decorative-glass-bottle.html": "Gothic Romance Hand-Decorated Glass Bottle · Gothic Decor · TRESORA",
    "products/klimt-the-kiss-gift-box.html": "Klimt The Kiss Gift Box · Gift for Art Lovers · TRESORA",
    "products/new-york-gift-box.html": "New York Gift Box · NYC Gift Set for Her · TRESORA",
    "products/paris-gift-box.html": "Paris Gift Box for Her · Pearl & Lace Gift Set · TRESORA",
    "products/rococo-reverie-decorative-glass-bottle.html": "Rococo Reverie Hand-Decorated Glass Bottle · TRESORA",
    "products/sargent-the-wineglasses-wine-gift-box.html": "Sargent The Wineglasses Wine Gift Box · TRESORA",
    "products/van-gogh-almond-blossom-gift-box.html": "Van Gogh Almond Blossom Gift Box · Gift for Art Lovers · TRESORA",
    "products/vermeer-girl-with-a-pearl-earring-gift-box.html": "Vermeer Girl with a Pearl Earring Gift Box · TRESORA",
    "products/vintage-christmas-decoupage-ornaments.html": "Handmade Vintage Christmas Ornaments Gift Set · TRESORA"
  };
  var DESCS = {
    "index.html": "Gift boxes inspired by Klimt, Van Gogh, Vermeer, Paris and Amalfi, plus hand-decorated glass for the home. Ready to give. Free US shipping.",
    "shop.html": "Shop all TRESORA gifts: art-inspired and city-inspired gift boxes and handcrafted glass for the home. Gift-ready, with free US shipping.",
    "about.html": "TRESORA makes gift boxes inspired by art and cities, and hand-decorated glass for the home. Shipped free across the US from Los Angeles.",
    "contact.html": "Questions about an order or a gift? Contact TRESORA, the art- and city-inspired gift box studio in Los Angeles.",
    "faq.html": "Answers about TRESORA gift boxes: what is inside, gift-ready packaging, free US shipping, returns and secure Stripe checkout.",
    "shipping.html": "Free US shipping on every TRESORA order, sent from Los Angeles. Processing and delivery times explained.",
    "returns.html": "TRESORA refund and return policy: how to request a return or refund for your gift box, and the conditions that apply."
  };

  function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
  function unesc(s) { return String(s).replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&"); }
  function abs(u) { return /^https?:/.test(u) ? u : SITE + (u.charAt(0) === "/" ? "" : "/") + u; }
  function pageUrl(path) { return path === "index.html" ? SITE + "/" : SITE + "/" + path; }
  function m(re, s) { var x = re.exec(s); return x ? x[1] : null; }
  function ld(obj) { return '<script type="application/ld+json" data-seo>' + JSON.stringify(obj).replace(/</g, "\\u003c") + "</script>"; }

  function transform(path, html) {
    var s = html;
    // strip anything this pass added before (idempotent) and the old tresora.store canonical
    s = s.replace(/<link rel="canonical"[^>]*>\n?/g, "");
    s = s.replace(/<meta (property|name)="(og|twitter):[^>]*data-seo>\n?/g, "");
    s = s.replace(/<meta name="robots"[^>]*data-seo>\n?/g, "");
    s = s.replace(/<script type="application\/ld\+json" data-seo>[\s\S]*?<\/script>\n?/g, "");

    if (TITLES[path]) s = s.replace(/<title>[^<]*<\/title>/, "<title>" + esc(TITLES[path]) + "</title>");
    if (DESCS[path]) s = s.replace(/<meta name="description" content="[^"]*">/, '<meta name="description" content="' + esc(DESCS[path]) + '">');

    var head = [];
    if (NOINDEX.indexOf(path) >= 0) {
      head.push('<meta name="robots" content="noindex, follow" data-seo>');
      return s.replace("</head>", head.join("\n") + "\n</head>");
    }
    var url = pageUrl(path);
    var title = unesc(m(/<title>([^<]*)<\/title>/, s) || "TRESORA");
    var desc = unesc(m(/<meta name="description" content="([^"]*)"/, s) || "");
    var isProduct = path.indexOf("products/") === 0;
    var mainImg = isProduct ? m(/<img src="([^"]+)"[^>]*data-rd-main/, s) : null;
    var img = abs(mainImg || DEFAULT_IMG);

    head.push('<link rel="canonical" href="' + url + '">');
    head.push('<meta property="og:site_name" content="TRESORA" data-seo>');
    head.push('<meta property="og:type" content="' + (isProduct ? "product" : "website") + '" data-seo>');
    head.push('<meta property="og:title" content="' + esc(title) + '" data-seo>');
    head.push('<meta property="og:description" content="' + esc(desc) + '" data-seo>');
    head.push('<meta property="og:url" content="' + url + '" data-seo>');
    head.push('<meta property="og:image" content="' + img + '" data-seo>');
    head.push('<meta name="twitter:card" content="summary_large_image" data-seo>');

    if (path === "index.html") {
      head.push(ld({ "@context": "https://schema.org", "@graph": [
        { "@type": "Organization", "@id": SITE + "/#org", name: "TRESORA", url: SITE + "/",
          logo: SITE + "/redesign/shared/img/logo-dark.png", sameAs: SAME_AS },
        { "@type": "WebSite", "@id": SITE + "/#website", name: "TRESORA", url: SITE + "/", publisher: { "@id": SITE + "/#org" },
          potentialAction: { "@type": "SearchAction", target: SITE + "/shop.html?q={search_term_string}", "query-input": "required name=search_term_string" } }
      ] }));
    }

    if (isProduct) {
      var name = unesc(m(/<div class="rd-pdp__info">[\s\S]*?<h1>([^<]*)<\/h1>/, s) || title);
      var priceTxt = m(/data-rd-price>\$([0-9.,]+)</, s) || "";
      var sku = m(/data-rd-add="([^"]+)"/, s);
      var soldOut = /rd-pdp__main"><span class="rd-badge">Sold out/.test(s);
      var gal = m(/<div class="rd-pdp__gallery">([\s\S]*?)<div class="rd-pdp__info">/, s) || "";
      var imgs = [], re = /<img src="([^"]+)"/g, x;
      while ((x = re.exec(gal))) { var u = abs(x[1].replace(/-t(\.\w+)$/, "$1")); if (imgs.indexOf(u) < 0) imgs.push(u); }
      if (!imgs.length) imgs.push(img);
      var crumbs = m(/<nav class="rd-crumbs"[^>]*>([\s\S]*?)<\/nav>/, s) || "";
      var items = [], cr = /<a href="([^"]+)">([^<]*)<\/a>/g, c, pos = 1;
      while ((c = cr.exec(crumbs))) items.push({ "@type": "ListItem", position: pos++, name: unesc(c[2]), item: abs(c[1]) });
      items.push({ "@type": "ListItem", position: pos, name: name, item: url });
      var offer = { "@type": "Offer", url: url, priceCurrency: "USD", price: priceTxt.replace(/,/g, ""),
        availability: soldOut ? "https://schema.org/OutOfStock" : "https://schema.org/InStock",
        itemCondition: "https://schema.org/NewCondition", seller: { "@type": "Organization", name: "TRESORA" },
        shippingDetails: { "@type": "OfferShippingDetails", shippingRate: { "@type": "MonetaryAmount", value: "0", currency: "USD" },
          shippingDestination: { "@type": "DefinedRegion", addressCountry: "US" } } };
      var product = { "@context": "https://schema.org", "@type": "Product", name: name, description: desc, image: imgs,
        brand: { "@type": "Brand", name: "TRESORA" }, url: url, offers: offer };
      if (sku) product.sku = sku;
      head.push(ld(product));
      head.push(ld({ "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: items }));

      // alt text on gallery thumbnails
      var n = 0;
      s = s.replace(/<div class="rd-pdp__gallery">[\s\S]*?<div class="rd-pdp__info">/, function (block) {
        return block.replace(/<img src="([^"]+)" alt=""/g, function (all, src) {
          n++; return '<img src="' + src + '" alt="' + esc(name) + " – photo " + n + '"';
        });
      });
    }
    return s.replace("</head>", head.join("\n") + "\n</head>");
  }

  function sitemap(paths, date) {
    var urls = paths.filter(function (p) { return NOINDEX.indexOf(p) < 0; }).sort(function (a, b) {
      var r = function (p) { return p === "index.html" ? 0 : p === "shop.html" ? 1 : p.indexOf("products/") === 0 ? 2 : p.indexOf("blog") === 0 ? 3 : 4; };
      return r(a) - r(b) || (a < b ? -1 : 1);
    });
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
      urls.map(function (p) { return "  <url><loc>" + pageUrl(p) + "</loc><lastmod>" + date + "</lastmod></url>"; }).join("\n") + "\n</urlset>\n";
  }

  root.seoTransform = transform; root.seoSitemap = sitemap; root.SEO_NOINDEX = NOINDEX;

  if (typeof module !== "undefined" && require.main === module) {
    var fs = require("fs"), p = require("path");
    var pages = ["index.html", "shop.html", "about.html", "contact.html", "faq.html", "shipping.html", "returns.html",
      "privacy.html", "terms.html"].concat(NOINDEX)
      .concat(fs.readdirSync("products").filter(function (f) { return /\.html$/.test(f); }).map(function (f) { return "products/" + f; }))
      .concat(fs.existsSync("blog") ? fs.readdirSync("blog").filter(function (f) { return /\.html$/.test(f); }).map(function (f) { return "blog/" + f; }) : [])
      .filter(function (f) { return fs.existsSync(f); });
    pages.forEach(function (f) {
      var a = fs.readFileSync(f, "utf8"), b = transform(f, a);
      if (a !== b) { fs.writeFileSync(f, b); console.log("updated", f); }
    });
    fs.writeFileSync("sitemap.xml", sitemap(pages, new Date().toISOString().slice(0, 10)));
    console.log("wrote sitemap.xml");
  }
})(typeof window !== "undefined" ? window : globalThis);
