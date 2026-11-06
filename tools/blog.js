/* TRESORA Journal (blog) builder.
   Source: blog/posts/<slug>.html — an HTML fragment that starts with a JSON header comment:
     <!--{"title":"…","seoTitle":"…","description":"…","date":"YYYY-MM-DD","image":"/redesign/shared/products/x-0.jpg","imageAlt":"…"}-->
   Output: blog/<slug>.html for every post + blog/index.html (newest first). Header/footer come from about.html.
   Run from the repo root:  node tools/blog.js && node tools/seo_pass.js */
var fs = require("fs");
var SITE = "https://tresoragift.com";
function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
function fmt(d) { var m = ["January","February","March","April","May","June","July","August","September","October","November","December"];
  var p = d.split("-"); return m[+p[1] - 1] + " " + (+p[2]) + ", " + p[0]; }

var shell = fs.readFileSync("about.html", "utf8");
var headEnd = shell.indexOf("</head>");
var mainStart = shell.indexOf('<main id="main">');
var footStart = shell.indexOf('<footer class="rd-footer">');
var HEAD = shell.slice(0, headEnd)
  .replace(/<link rel="canonical"[^>]*>\n?/g, "")
  .replace(/<meta (property|name)="(og|twitter):[^>]*data-seo>\n?/g, "")
  .replace(/<script type="application\/ld\+json"[^>]*>[\s\S]*?<\/script>\n?/g, "")
  .replace('class="rd rd-v4 rd-page--legal"', 'class="rd rd-v4 rd-page--legal rd-page--blog"');
var BODY_TOP = shell.slice(headEnd, mainStart);
var FOOT = shell.slice(footStart);
var STYLE = "<style>.rd-blog .rd-legal__body{max-width:72ch}.rd-blog__meta{color:var(--muted,#6b625a);font-size:13px;letter-spacing:.06em;text-transform:uppercase;margin:6px 0 0}" +
  ".rd-blog__hero{margin:0 0 28px}.rd-blog__hero img,.rd-blog figure img{display:block;width:100%;height:auto;border-radius:2px}" +
  ".rd-blog figure{margin:22px 0}.rd-blog figcaption{font-size:13px;color:var(--muted,#6b625a);margin-top:8px}" +
  ".rd-blog h3{font:400 20px/1.35 var(--head);margin:28px 0 8px}.rd-blog table{width:100%;border-collapse:collapse;margin:8px 0 20px;font-size:14px}" +
  ".rd-blog th,.rd-blog td{border-bottom:1px solid rgba(0,0,0,.12);padding:10px 8px;text-align:left;vertical-align:top}" +
  ".rd-blog__cta{margin:30px 0 0}.rd-blog__cta a{display:inline-block;padding:13px 22px;border:1px solid var(--ink);text-decoration:none;letter-spacing:.08em;text-transform:uppercase;font-size:13px}" +
  ".rd-blog__list{list-style:none;padding:0;margin:0;display:grid;gap:34px}.rd-blog__list li{margin:0}.rd-blog__list a.rd-blog__card{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;text-decoration:none;color:inherit}" +
  "@media(min-width:720px){.rd-blog__list a.rd-blog__card{grid-template-columns:260px minmax(0,1fr);gap:24px;align-items:start}}" +
  ".rd-blog__list img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover}.rd-blog__list h2{margin:0 0 6px!important}</style>";

function page(o) {
  return HEAD.replace(/<title>[^<]*<\/title>/, "<title>" + esc(o.seoTitle) + "</title>")
    .replace(/<meta name="description" content="[^"]*">/, '<meta name="description" content="' + esc(o.description) + '">') +
    (o.ogImage ? '<meta name="tresora:image" content="' + esc(o.ogImage) + '">\n' : "") + STYLE + "\n" + (o.ld || "") + "\n" +
    BODY_TOP + '<main id="main">' + o.main + "</main>\n" + FOOT;
}

var dir = "blog/posts";
var posts = fs.readdirSync(dir).filter(function (f) { return /\.html$/.test(f); }).map(function (f) {
  var src = fs.readFileSync(dir + "/" + f, "utf8"); var m = /^<!--(\{[\s\S]*?\})-->\s*/.exec(src);
  if (!m) throw new Error("missing JSON header in " + f);
  var meta = JSON.parse(m[1]); meta.slug = f.replace(/\.html$/, ""); meta.body = src.slice(m[0].length); return meta;
}).sort(function (a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : (a.slug < b.slug ? -1 : 1); });

posts.forEach(function (p) {
  var url = SITE + "/blog/" + p.slug + ".html";
  var ld = '<script type="application/ld+json" data-blog>' + JSON.stringify({ "@context": "https://schema.org", "@type": "BlogPosting",
    headline: p.title, description: p.description, image: [SITE + p.image], datePublished: p.date, dateModified: p.updated || p.date,
    author: { "@type": "Organization", name: "TRESORA", url: SITE + "/" }, publisher: { "@type": "Organization", name: "TRESORA",
      logo: { "@type": "ImageObject", url: SITE + "/redesign/shared/img/logo-dark.png" } }, mainEntityOfPage: url }).replace(/</g, "\\u003c") + "</script>";
  var more = posts.filter(function (q) { return q.slug !== p.slug; }).slice(0, 4).map(function (q) {
    return '<a href="/blog/' + q.slug + '.html">' + esc(q.title) + "</a>"; }).join("");
  var main = '<section class="rd-section rd-pagehead"><nav class="rd-crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="rd-crumbs__sep">/</span>' +
    '<a href="/blog/">Journal</a><span class="rd-crumbs__sep">/</span><span aria-current="page">' + esc(p.title) + "</span></nav><h1>" + esc(p.title) +
    '</h1><p class="rd-blog__meta">TRESORA Journal · <time datetime="' + p.date + '">' + fmt(p.date) + "</time></p></section>\n" +
    '<section class="rd-section rd-legal rd-blog"><article class="rd-legal__body"><figure class="rd-blog__hero"><img src="' + esc(p.image) + '" alt="' + esc(p.imageAlt || p.title) +
    '" loading="eager" decoding="async"></figure>\n' + p.body + "\n</article>\n" +
    '<nav class="rd-legal__more" aria-label="More from the Journal"><h2>More from the Journal</h2>' + more + '<a href="/blog/">All articles</a><a href="/shop.html">Shop all gifts</a></nav></section>\n';
  fs.writeFileSync("blog/" + p.slug + ".html", page({ seoTitle: p.seoTitle || p.title + " · TRESORA", description: p.description, ogImage: p.image, ld: ld, main: main }));
  console.log("wrote blog/" + p.slug + ".html");
});

var list = posts.map(function (p) {
  return '<li><a class="rd-blog__card" href="/blog/' + p.slug + '.html"><img src="' + esc(p.image) + '" alt="' + esc(p.imageAlt || p.title) + '" loading="lazy" decoding="async">' +
    '<div><p class="rd-blog__meta"><time datetime="' + p.date + '">' + fmt(p.date) + "</time></p><h2>" + esc(p.title) + "</h2><p>" + esc(p.description) + "</p></div></a></li>";
}).join("\n");
fs.writeFileSync("blog/index.html", page({
  seoTitle: "TRESORA Journal · Gift Guides & Ideas for Art and City Lovers",
  description: "Gift guides and ideas from TRESORA: gifts for art lovers, wine lovers, Christmas and every occasion, with art- and city-inspired gift boxes.",
  ogImage: posts.length ? posts[0].image : null,
  main: '<section class="rd-section rd-pagehead"><nav class="rd-crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span class="rd-crumbs__sep">/</span><span aria-current="page">Journal</span></nav>' +
    "<h1>The TRESORA Journal</h1></section>\n" + '<section class="rd-section rd-legal rd-blog"><div class="rd-legal__body"><p>Gift guides, stories behind the paintings and cities in our boxes, and ideas for every occasion.</p>' +
    '<ul class="rd-blog__list">' + list + "</ul></div></section>\n"
}));
console.log("wrote blog/index.html (" + posts.length + " posts)");
