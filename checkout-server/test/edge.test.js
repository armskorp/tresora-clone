import test from "node:test";
import assert from "node:assert/strict";
import { buildLines, sessionParams } from "../../supabase/functions/checkout/lib.js";
const KLIMT = "44325276582001", CROW = "67725560053873";
test("server prices + personalization", () => {
  const { lines, error } = buildLines({ items: [{ variant_id: Number(KLIMT), quantity: 2, unit_amount: 1, personalization: { card: "birthday", message: "Love you", lid: "ANNA" } }, { variant_id: Number(CROW), quantity: 1 }] });
  assert.equal(error, undefined);
  const p = sessionParams(lines, "https://tresoragift.com");
  assert.equal(p.get("line_items[0][price_data][unit_amount]"), "5900");
  assert.equal(p.get("line_items[1][price_data][unit_amount]"), "4000");
  assert.match(p.get("line_items[0][price_data][product_data][description]"), /Happy Birthday.*Love you.*ANNA/);
  assert.match(p.get("metadata[item_1]"), /Box lid: "ANNA"/);
  assert.equal(p.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]"), "0");
});
test("validation", () => {
  assert.ok(buildLines({ items: [{ variant_id: Number(KLIMT), quantity: 1, personalization: { lid: "x".repeat(21) } }] }).error);
  assert.ok(buildLines({ items: [{ variant_id: Number(CROW), quantity: 1, personalization: { lid: "A" } }] }).error);
  assert.ok(buildLines({ items: [{ variant_id: Number(KLIMT), quantity: 1, personalization: { card: "bogus" } }] }).error);
  assert.ok(buildLines({ items: [{ variant_id: Number(KLIMT), quantity: 1, personalization: { message: "m".repeat(256) } }] }).error);
});
