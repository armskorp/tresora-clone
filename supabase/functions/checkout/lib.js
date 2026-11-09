/* TRESORA checkout core (shared by the Supabase edge function). Plain JS so it runs in Deno and Node tests.
   Prices/names/availability come ONLY from ./catalog.js. Client prices are ignored. */
import catalog from "./catalog.js";

export const MAX_LINES = 25, MAX_QTY = 20, LID_MAX = 20, MSG_MAX = 255;
export const CARDS = { nocard: "No Card (Blank / None)", birthday: "Happy Birthday", anniversary: "Anniversary", thankyou: "Thank You", congrats: "Congratulations", justbecause: "Just Because" };
export const hasLid = (v) => /gift box/i.test(v.name);
const clean = (s) => String(s == null ? "" : s).replace(/[\u0000-\u001f\u007f]+/g, " ").replace(/\s+/g, " ").trim();

/** Validate cart. Returns {lines} or {error}. Lines with the same variant AND same personalization are merged. */
export function buildLines(payload, cat = catalog) {
  if (!payload || !Array.isArray(payload.items) || payload.items.length === 0) return { error: "Cart is empty" };
  if (payload.items.length > MAX_LINES) return { error: "Too many items" };
  const merged = new Map();
  for (const item of payload.items) {
    const id = String(item && item.variant_id), qty = item && item.quantity;
    if (!/^\d+$/.test(id)) return { error: "Invalid item" };
    if (!Number.isInteger(qty) || qty < 1 || qty > MAX_QTY) return { error: "Invalid quantity" };
    const v = cat.variants[id];
    if (!v) return { error: "Unknown product" };
    if (!v.available) return { error: `${v.name} is sold out` };
    if (item.product_id !== undefined && String(item.product_id) !== String(v.product_id)) return { error: "Invalid item" };
    const p = item.personalization || {};
    const card = p.card ? String(p.card) : "";
    if (card && !CARDS[card]) return { error: "Invalid greeting card" };
    const message = clean(p.message), lid = clean(p.lid);
    if (message.length > MSG_MAX) return { error: `Card message must be ${MSG_MAX} characters or fewer` };
    if (lid.length > LID_MAX) return { error: `Box lid inscription must be ${LID_MAX} characters or fewer` };
    if (lid && !hasLid(v)) return { error: "Box lid inscription is not available for this item" };
    const pers = { card, message, lid };
    const key = id + "|" + JSON.stringify(pers);
    const prev = merged.get(key);
    merged.set(key, { id, ...v, pers, quantity: Math.min(MAX_QTY, (prev ? prev.quantity : 0) + qty) });
  }
  return { lines: [...merged.values()] };
}

export function persText(p) {
  const out = [];
  if (p.card) out.push(`Greeting card: ${CARDS[p.card]}`);
  if (p.message) out.push(`Card message: "${p.message}"`);
  if (p.lid) out.push(`Box lid: "${p.lid}"`);
  return out.join(" | ");
}

/** Stripe Checkout Session params (x-www-form-urlencoded). */
export function sessionParams(lines, site, currency = catalog.currency || "usd") {
  site = String(site).replace(/\/+$/, "");
  const p = new URLSearchParams();
  p.set("mode", "payment");
  p.set("success_url", `${site}/success.html?session_id={CHECKOUT_SESSION_ID}`);
  p.set("cancel_url", `${site}/cancel.html`);
  p.set("shipping_address_collection[allowed_countries][0]", "US");
  p.set("shipping_options[0][shipping_rate_data][type]", "fixed_amount");
  p.set("shipping_options[0][shipping_rate_data][display_name]", "Free US shipping");
  p.set("shipping_options[0][shipping_rate_data][fixed_amount][amount]", "0");
  p.set("shipping_options[0][shipping_rate_data][fixed_amount][currency]", currency);
  p.set("billing_address_collection", "auto");
  p.set("customer_creation", "always"); // email is always collected by Checkout; also saves a Customer
  p.set("phone_number_collection[enabled]", "true");
  p.set("allow_promotion_codes", "true"); // customers can enter codes such as WELCOME15 (welcome popup)
  // no payment_method_types -> dynamic/automatic payment methods (cards, Apple Pay, Google Pay, ...) from Dashboard settings
  const summary = [];
  lines.forEach((l, i) => {
    const k = `line_items[${i}]`, t = persText(l.pers);
    p.set(`${k}[quantity]`, String(l.quantity));
    p.set(`${k}[price_data][currency]`, currency);
    p.set(`${k}[price_data][unit_amount]`, String(l.unit_amount));
    p.set(`${k}[price_data][product_data][name]`, l.name);
    if (t) p.set(`${k}[price_data][product_data][description]`, t);
    if (l.image) p.set(`${k}[price_data][product_data][images][0]`, l.image);
    p.set(`${k}[price_data][product_data][metadata][variant_id]`, l.id);
    p.set(`${k}[price_data][product_data][metadata][product_id]`, String(l.product_id));
    if (l.pers.card) p.set(`${k}[price_data][product_data][metadata][greeting_card]`, CARDS[l.pers.card]);
    if (l.pers.message) p.set(`${k}[price_data][product_data][metadata][card_message]`, l.pers.message);
    if (l.pers.lid) p.set(`${k}[price_data][product_data][metadata][box_lid]`, l.pers.lid);
    const line = `${l.name} x${l.quantity}${t ? " — " + t : ""}`.slice(0, 500);
    summary.push(line);
    p.set(`metadata[item_${i + 1}]`, line);
    p.set(`payment_intent_data[metadata][item_${i + 1}]`, line);
  });
  const cart = lines.map((l) => `${l.id}x${l.quantity}`).join(",").slice(0, 500);
  p.set("metadata[cart]", cart);
  p.set("payment_intent_data[metadata][cart]", cart);
  p.set("payment_intent_data[description]", summary.join(" ; ").slice(0, 1000));
  return p;
}
