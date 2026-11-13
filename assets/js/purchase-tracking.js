/* TRESORA purchase tracking – loaded only on success.html (Stripe redirects here after payment:
   success.html?session_id={CHECKOUT_SESSION_ID}, both from the checkout edge function and from every live Payment Link).

   - GA4 (G-P2VCZH3M16): sends a "purchase" event once per Stripe Checkout Session.
   - Google Ads (AW-18553006418): sends the purchase conversion only when ADS_PURCHASE_LABEL is filled in.
     Copy the label from Google Ads > Goals > Conversions > "Покупка" > Tag setup > "Use Google tag":
     send_to: 'AW-18553006418/XXXXXXXXXXXX'  ->  ADS_PURCHASE_LABEL = 'XXXXXXXXXXXX'.
     (Alternatively import the GA4 "purchase" key event into Google Ads and leave the label empty.)
   - value/currency/items come from the cart saved by assets/js/cart.js right before the Stripe redirect
     (catalog display prices, before promotion codes). If nothing was saved (e.g. other device), the event goes out without a value.
   - Fires only for a real-looking session id (cs_live_/cs_test_) and never twice for the same id (localStorage), so reloads don't double-count. */
(function () {
  'use strict';
  var ADS_ID = 'AW-18553006418';
  var ADS_PURCHASE_LABEL = ''; // <- conversion label of the "Покупка" action; empty = Google Ads conversion is not sent from here
  var PENDING_KEY = 'tresora_pending_purchase';
  var DONE_KEY = 'tresora_tracked_purchases';
  var MAX_AGE = 48 * 3600 * 1000;

  if (typeof window.gtag !== 'function') return;
  var sid = '';
  try { sid = new URLSearchParams(location.search).get('session_id') || ''; } catch (e) { return; }
  if (!/^cs_(live|test)_[A-Za-z0-9]+$/.test(sid)) return;

  var store = null;
  try { store = window.localStorage; } catch (e) { store = null; }
  var done = [];
  if (store) { try { done = JSON.parse(store.getItem(DONE_KEY) || '[]'); } catch (e) { done = []; } }
  if (!Array.isArray(done)) done = [];
  if (done.indexOf(sid) !== -1) return;

  var pending = null;
  if (store) { try { pending = JSON.parse(store.getItem(PENDING_KEY) || 'null'); } catch (e) { pending = null; } }
  if (!pending || typeof pending.value !== 'number' || !(pending.value > 0) || !pending.ts || Date.now() - pending.ts > MAX_AGE) pending = null;

  var ev = { transaction_id: sid };
  if (pending) {
    ev.value = pending.value;
    ev.currency = pending.currency || 'USD';
    ev.shipping = 0;
    if (Array.isArray(pending.items)) ev.items = pending.items;
  }
  window.gtag('event', 'purchase', ev);

  if (ADS_PURCHASE_LABEL) {
    var conv = { send_to: ADS_ID + '/' + ADS_PURCHASE_LABEL, transaction_id: sid };
    if (pending) { conv.value = pending.value; conv.currency = ev.currency; }
    window.gtag('event', 'conversion', conv);
  }

  if (store) {
    try {
      done.push(sid);
      store.setItem(DONE_KEY, JSON.stringify(done.slice(-50)));
      store.removeItem(PENDING_KEY);
    } catch (e) { /* ignore */ }
  }
})();
