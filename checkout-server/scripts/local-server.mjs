// Local integration harness: serves the Worker on http://127.0.0.1:8787 with Stripe MOCKED
// (no keys, no network). The mock "Checkout URL" sends the browser straight to the site's success page.
//   node scripts/local-server.mjs              (Stripe mocked)
//   REAL_STRIPE=1 node scripts/local-server.mjs (real Stripe TEST API, reads STRIPE_SECRET_KEY from env)
import http from "node:http";
import worker from "../src/index.js";
const SITE = process.env.SITE_URL || "http://127.0.0.1:8765";
const REAL = process.env.REAL_STRIPE === "1";
if (REAL && !String(process.env.STRIPE_SECRET_KEY || "").startsWith("sk_test_")) { console.error("REAL_STRIPE=1 needs a sk_test_ key in STRIPE_SECRET_KEY"); process.exit(1); }
const env = { STRIPE_SECRET_KEY: REAL ? process.env.STRIPE_SECRET_KEY : "sk_test_mock", SITE_URL: SITE, ALLOWED_ORIGINS: SITE };
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, init) => {
  if (!REAL && String(url).startsWith("https://api.stripe.com/")) {
    const p = new URLSearchParams(init.body.toString());
    console.log("[mock stripe] session:", [...p].filter(([k]) => /unit_amount|quantity|\[name\]/.test(k)).map(([k, v]) => `${k.replace("price_data][", "")}=${v}`).join("  "));
    return new Response(JSON.stringify({ url: p.get("success_url").replace("{CHECKOUT_SESSION_ID}", "cs_test_mock") }), { status: 200 });
  }
  return realFetch(url, init);
};
http.createServer(async (req, res) => {
  const chunks = []; for await (const c of req) chunks.push(c);
  const body = chunks.length ? Buffer.concat(chunks) : undefined;
  const r = await worker.fetch(new Request("http://127.0.0.1:8787" + req.url, { method: req.method, headers: req.headers, body: ["GET", "HEAD"].includes(req.method) ? undefined : body }), env);
  res.writeHead(r.status, Object.fromEntries(r.headers)); res.end(Buffer.from(await r.arrayBuffer()));
}).listen(8787, "127.0.0.1", () => console.log("worker on http://127.0.0.1:8787 " + (REAL ? "(REAL Stripe test mode)" : "(Stripe mocked)")));
