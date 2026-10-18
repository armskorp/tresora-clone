// Run: npm test  (Node 18+). Stripe is mocked; no network or keys needed.
import test from "node:test";
import assert from "node:assert/strict";
import worker, { buildLines } from "../src/index.js";
import catalog from "../src/catalog.js";

const ENV = { STRIPE_SECRET_KEY: "sk_test_dummy", SITE_URL: "https://armskorp.github.io/tresora-clone", ALLOWED_ORIGINS: "https://armskorp.github.io" };
const ORIGIN = "https://armskorp.github.io";
const KLIMT = "44325276582001";        // $59.00
const CARAVAGGIO_RED = "44325380423793"; // $69.00
const SOLD_OUT = Object.keys(catalog.variants).find((k) => !catalog.variants[k].available);

function req(body, { origin = ORIGIN, method = "POST", path = "/checkout" } = {}) {
  return new Request("https://worker.example" + path, { method, headers: { Origin: origin, "Content-Type": "application/json" }, body: method === "POST" ? JSON.stringify(body) : undefined });
}
function mockStripe() {
  const calls = [];
  globalThis.fetch = async (url, init) => { calls.push({ url, init, params: new URLSearchParams(init.body.toString()) }); return new Response(JSON.stringify({ id: "cs_test_1", url: "https://checkout.stripe.com/c/pay/cs_test_1" }), { status: 200 }); };
  return calls;
}

test("creates a session using SERVER prices, ignoring client prices", async () => {
  const calls = mockStripe();
  const res = await worker.fetch(req({ items: [{ variant_id: Number(KLIMT), quantity: 2, price: 1, unit_amount: 1 }, { variant_id: Number(CARAVAGGIO_RED), product_id: 7813867307121, quantity: 1 }] }), ENV);
  assert.equal(res.status, 200);
  assert.equal((await res.json()).url, "https://checkout.stripe.com/c/pay/cs_test_1");
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  const p = calls[0].params;
  assert.equal(calls[0].url, "https://api.stripe.com/v1/checkout/sessions");
  assert.equal(calls[0].init.headers.Authorization, "Bearer sk_test_dummy");
  assert.equal(p.get("mode"), "payment");
  assert.equal(p.get("line_items[0][price_data][unit_amount]"), "5900");
  assert.equal(p.get("line_items[0][quantity]"), "2");
  assert.equal(p.get("line_items[1][price_data][unit_amount]"), "6900");
  assert.equal(p.get("line_items[1][price_data][product_data][name]"), "Caravaggio Bacchus Wine Gift Box – Red");
  assert.equal(p.get("line_items[0][price_data][currency]"), "usd");
  assert.equal(p.get("success_url"), "https://armskorp.github.io/tresora-clone/success.html?session_id={CHECKOUT_SESSION_ID}");
  assert.equal(p.get("cancel_url"), "https://armskorp.github.io/tresora-clone/cancel.html");
});

test("merges duplicate lines", () => {
  const { lines } = buildLines({ items: [{ variant_id: KLIMT, quantity: 1 }, { variant_id: KLIMT, quantity: 2 }] });
  assert.equal(lines.length, 1); assert.equal(lines[0].quantity, 3);
});

test("rejects bad input", async () => {
  mockStripe();
  const cases = [
    [{ items: [] }, 400], [{}, 400],
    [{ items: [{ variant_id: 123, quantity: 1 }] }, 400],
    [{ items: [{ variant_id: KLIMT, quantity: 0 }] }, 400],
    [{ items: [{ variant_id: KLIMT, quantity: 21 }] }, 400],
    [{ items: [{ variant_id: KLIMT, quantity: 1.5 }] }, 400],
    [{ items: [{ variant_id: KLIMT, quantity: "2" }] }, 400],
    [{ items: [{ variant_id: KLIMT, product_id: 1, quantity: 1 }] }, 400],
  ];
  if (SOLD_OUT) cases.push([{ items: [{ variant_id: SOLD_OUT, quantity: 1 }] }, 400]);
  for (const [body, status] of cases) assert.equal((await worker.fetch(req(body), ENV)).status, status, JSON.stringify(body));
});

test("blocks other origins, handles preflight, requires config", async () => {
  mockStripe();
  assert.equal((await worker.fetch(req({ items: [{ variant_id: KLIMT, quantity: 1 }] }, { origin: "https://evil.example" }), ENV)).status, 403);
  const pre = await worker.fetch(new Request("https://worker.example/checkout", { method: "OPTIONS", headers: { Origin: ORIGIN } }), ENV);
  assert.equal(pre.status, 204); assert.equal(pre.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  assert.equal((await worker.fetch(req({ items: [{ variant_id: KLIMT, quantity: 1 }] }), { ...ENV, STRIPE_SECRET_KEY: "" })).status, 503);
  assert.equal((await worker.fetch(req(null, { method: "GET", path: "/health" }), ENV)).status, 200);
});

test("Stripe failure returns 502 without leaking details", async () => {
  globalThis.fetch = async () => new Response(JSON.stringify({ error: { message: "Invalid API Key provided: sk_test_***" } }), { status: 401 });
  const res = await worker.fetch(req({ items: [{ variant_id: KLIMT, quantity: 1 }] }), ENV);
  assert.equal(res.status, 502); assert.deepEqual(await res.json(), { error: "Payment provider error" });
});
