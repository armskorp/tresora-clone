// Supabase Edge Function "checkout": creates ONE Stripe Checkout Session for the whole TRESORA cart.
// POST {items:[{variant_id, product_id, quantity, personalization:{card,message,lid}}]} -> {url}
// Secret: STRIPE_SECRET_KEY (function env). Fallback: Supabase Vault secret "stripe_secret_key" read via
// the service-role-only RPC public.get_stripe_secret(). The key is never in code or the repo.
import { buildLines, sessionParams } from "./lib.js";

const ALLOWED = ["https://tresoragift.com", "https://www.tresoragift.com"];
const SITE = "https://tresoragift.com";
const MAX_BODY = 20_000;

function cors(origin: string) {
  const h: Record<string, string> = { "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400", Vary: "Origin" };
  if (ALLOWED.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}
const json = (b: unknown, s: number, h: Record<string, string>) => new Response(JSON.stringify(b), { status: s, headers: { "Content-Type": "application/json", ...h } });

let cachedKey = "";
async function stripeKey(): Promise<string> {
  if (cachedKey) return cachedKey;
  const env = Deno.env.get("STRIPE_SECRET_KEY");
  if (env) return (cachedKey = env.trim());
  const url = Deno.env.get("SUPABASE_URL"), srk = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !srk) return "";
  const r = await fetch(`${url}/rest/v1/rpc/get_stripe_secret`, { method: "POST", headers: { apikey: srk, Authorization: `Bearer ${srk}`, "Content-Type": "application/json" }, body: "{}" });
  if (!r.ok) return "";
  const v = await r.json().catch(() => "");
  return (cachedKey = typeof v === "string" ? v.trim() : "");
}

Deno.serve(async (req: Request) => {
  const h = cors(req.headers.get("Origin") || "");
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: h });
  if (req.method === "GET") return json({ ok: true }, 200, h);
  if (req.method !== "POST") return json({ error: "Not found" }, 404, h);
  if (!h["Access-Control-Allow-Origin"]) return json({ error: "Origin not allowed" }, 403, h);
  const key = await stripeKey();
  if (!key) return json({ error: "Checkout is not configured" }, 503, h);
  const raw = await req.text();
  if (raw.length > MAX_BODY) return json({ error: "Request too large" }, 413, h);
  let payload;
  try { payload = JSON.parse(raw); } catch { return json({ error: "Invalid JSON" }, 400, h); }
  const { lines, error } = buildLines(payload);
  if (error) return json({ error }, 400, h);
  const res = await fetch("https://api.stripe.com/v1/checkout/sessions", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/x-www-form-urlencoded", "Stripe-Version": "2024-06-20" },
    body: sessionParams(lines, SITE),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || !data.url) {
    console.error("Stripe error", res.status, data?.error?.message);
    return json({ error: "Payment provider error" }, 502, h);
  }
  return json({ url: data.url, id: data.id }, 200, h);
});
