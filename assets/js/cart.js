/* TRESORA client-side cart.
   - Cart lines are stored in localStorage ("tresora_cart_v1") as [{variant_id, quantity}], so the cart is the same on every page and survives reloads.
   - Product data (titles, images, display prices) comes from window.TRESORA_CATALOG (assets/js/catalog.js).
     Prices here are for display only. The checkout backend looks up the real prices on the server.
   - Checkout POSTs {items:[{product_id, variant_id, quantity}]} to TRESORA_CONFIG.CHECKOUT_URL and expects {url} back
     (a Stripe Checkout URL). If CHECKOUT_URL is empty, it shows a "payments coming soon" message. */
(function () {
  'use strict';
  var KEY = 'tresora_cart_v1';
  var CAT = window.TRESORA_CATALOG || { products: {}, variants: {} };
  var CFG = window.TRESORA_CONFIG || {};
  var MAX = Number(CFG.MAX_QTY_PER_LINE) || 20;
  var PLMODE = (CFG.PAYMENT_LINKS || '').trim();
  var PL = PLMODE && window.TRESORA_PAYMENT_LINKS && window.TRESORA_PAYMENT_LINKS[PLMODE];
  if (PL && !Object.keys(PL).length) PL = null;
  var BASE = document.documentElement.getAttribute('data-base') || '';
  var fmt = function (c) { return '$' + (c / 100).toFixed(2) + ' ' + (CFG.CURRENCY || 'USD'); };
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]; }); };
  var clamp = function (n) { n = parseInt(n, 10); return isNaN(n) ? 1 : Math.max(1, Math.min(MAX, n)); };

  /* ---------- storage ---------- */
  function read() {
    var lines;
    try { lines = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { lines = []; }
    if (!Array.isArray(lines)) lines = [];
    return lines.filter(function (l) { return l && CAT.variants[String(l.variant_id)]; })
      .map(function (l) { return { variant_id: Number(l.variant_id), quantity: clamp(l.quantity) }; });
  }
  function write(lines) {
    try { localStorage.setItem(KEY, JSON.stringify(lines)); } catch (e) { /* private mode: cart is kept in memory only */ }
    memory = lines; render();
  }
  var memory = null;
  function lines() { return memory || (memory = read()); }

  var Cart = {
    items: function () { return lines().slice(); },
    count: function () { return lines().reduce(function (s, l) { return s + l.quantity; }, 0); },
    subtotal: function () { return lines().reduce(function (s, l) { return s + CAT.variants[l.variant_id].price * l.quantity; }, 0); },
    add: function (variantId, qty) {
      var v = CAT.variants[String(variantId)];
      if (!v || !v.available) return false;
      var ls = lines().slice(), q = clamp(qty || 1), hit = ls.find(function (l) { return l.variant_id === v.id; });
      if (hit) hit.quantity = clamp(hit.quantity + q); else ls.push({ variant_id: v.id, quantity: q });
      write(ls); return true;
    },
    set: function (variantId, qty) {
      var ls = lines().map(function (l) { return l.variant_id === Number(variantId) ? { variant_id: l.variant_id, quantity: clamp(qty) } : l; });
      write(ls);
    },
    remove: function (variantId) { write(lines().filter(function (l) { return l.variant_id !== Number(variantId); })); },
    clear: function () { write([]); }
  };
  window.TresoraCart = Cart;

  /* ---------- drawer markup ---------- */
  var root = document.createElement('div');
  root.className = 'tc-root';
  root.innerHTML =
    '<div class="tc-overlay" data-cart-close></div>' +
    '<aside class="tc-drawer" role="dialog" aria-modal="true" aria-labelledby="tc-title" tabindex="-1">' +
    '  <div class="tc-drawer__head"><h2 class="tc-drawer__title" id="tc-title">Cart<small data-tc-count></small></h2>' +
    '    <button class="tc-close" type="button" data-cart-close aria-label="Close cart">×</button></div>' +
    '  <ul class="tc-items" data-tc-items></ul>' +
    '  <div class="tc-empty" data-tc-empty><p>Your cart is empty</p><button class="tc-button" type="button" data-cart-close>Continue shopping</button></div>' +
    '  <div class="tc-foot" data-tc-foot>' +
    '    <div class="tc-subtotal"><span>Subtotal</span><strong data-tc-subtotal></strong></div>' +
    '    <p class="tc-note">Free US shipping on all orders. Taxes calculated at checkout.</p>' +
    '    <button class="tc-button tc-checkout" type="button" data-tc-checkout>Checkout</button>' +
    '    <p class="tc-msg" data-tc-msg role="status" hidden></p>' +
    '  </div>' +
    '</aside><div class="tc-toast" data-tc-toast role="status" aria-live="polite"></div>';
  document.body.appendChild(root);
  var $ = function (s) { return root.querySelector(s); };
  var drawer = $('.tc-drawer'), lastFocus = null;

  function open() {
    lastFocus = document.activeElement;
    document.documentElement.classList.add('tc-open');
    document.querySelectorAll('[data-testid="cart-drawer-trigger"],[data-cart-open]').forEach(function (b) { b.setAttribute('aria-expanded', 'true'); });
    setTimeout(function () { drawer.focus(); }, 30);
  }
  function close() {
    document.documentElement.classList.remove('tc-open');
    document.querySelectorAll('[data-testid="cart-drawer-trigger"],[data-cart-open]').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
    msg('');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  Cart.open = open; Cart.close = close;

  function msg(text) { var m = $('[data-tc-msg]'); m.textContent = text; m.hidden = !text; }
  var toastT;
  function toast(text) {
    var t = $('[data-tc-toast]'); t.textContent = text; t.classList.add('show');
    clearTimeout(toastT); toastT = setTimeout(function () { t.classList.remove('show'); }, 2200);
  }

  /* ---------- render ---------- */
  function render() {
    var ls = lines(), n = Cart.count();
    $('[data-tc-items]').innerHTML = ls.map(function (l) {
      var v = CAT.variants[l.variant_id], href = BASE + 'products/' + v.handle + '.html';
      return '<li class="tc-item" data-variant="' + v.id + '">' +
        '<a href="' + href + '"><img src="' + BASE + esc(v.thumb) + '" alt="" width="84" height="84" loading="lazy"></a>' +
        '<div><a class="tc-item__title" href="' + href + '">' + esc(v.title) + '</a>' +
        (v.variant_title ? '<div class="tc-item__variant">' + esc(v.variant_title) + '</div>' : '') +
        '<div class="tc-item__unit">' + fmt(v.price) + '</div>' +
        '<div class="tc-item__controls"><div class="tc-qty">' +
        '<button type="button" data-tc-dec aria-label="Decrease quantity of ' + esc(v.title) + '"' + (l.quantity <= 1 ? ' disabled' : '') + '>−</button>' +
        '<output aria-live="polite" aria-label="Quantity">' + l.quantity + '</output>' +
        '<button type="button" data-tc-inc aria-label="Increase quantity of ' + esc(v.title) + '"' + (l.quantity >= MAX ? ' disabled' : '') + '>+</button></div>' +
        '<button class="tc-link tc-item__remove" type="button" data-tc-remove>Remove</button></div></div>' +
        '<div class="tc-item__total">' + fmt(v.price * l.quantity) + '</div></li>';
    }).join('');
    $('[data-tc-empty]').hidden = ls.length > 0;
    $('[data-tc-empty]').style.display = ls.length ? 'none' : '';
    $('[data-tc-items]').style.display = ls.length ? '' : 'none';
    $('[data-tc-foot]').style.display = ls.length ? '' : 'none';
    $('[data-tc-count]').textContent = n ? '(' + n + ')' : '';
    $('[data-tc-subtotal]').textContent = fmt(Cart.subtotal());
    // homepage header (theme markup)
    document.querySelectorAll('cart-icon .cart-bubble').forEach(function (b) {
      b.classList.toggle('visually-hidden', n === 0);
      var c = b.querySelector('.cart-bubble__text-count');
      if (c) { c.textContent = n; c.classList.toggle('hidden', n === 0); }
    });
    document.querySelectorAll('[data-testid="cart-drawer-trigger"]').forEach(function (b) { b.setAttribute('aria-label', 'Cart, ' + n + ' item' + (n === 1 ? '' : 's')); });
    // standalone pages
    document.querySelectorAll('[data-cart-count]').forEach(function (b) { b.textContent = n; b.hidden = n === 0; });
  }

  /* ---------- drawer events ---------- */
  root.addEventListener('click', function (e) {
    var t = e.target;
    if (t.closest('[data-cart-close]')) { e.preventDefault(); close(); return; }
    var item = t.closest('.tc-item'); if (!item) {
      if (t.closest('[data-tc-checkout]')) checkout();
      return;
    }
    var id = Number(item.getAttribute('data-variant')), line = lines().find(function (l) { return l.variant_id === id; });
    if (!line) return;
    if (t.closest('[data-tc-inc]')) Cart.set(id, line.quantity + 1);
    else if (t.closest('[data-tc-dec]')) Cart.set(id, line.quantity - 1);
    else if (t.closest('[data-tc-remove]')) Cart.remove(id);
  });
  document.addEventListener('keydown', function (e) {
    if (!document.documentElement.classList.contains('tc-open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'Tab') { // keep focus inside the drawer
      var f = drawer.querySelectorAll('a[href],button:not([disabled]),input');
      f = Array.prototype.filter.call(f, function (el) { return el.offsetParent !== null; });
      if (!f.length) return;
      if (e.shiftKey && document.activeElement === f[0]) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && document.activeElement === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  });

  /* ---------- page integrations ---------- */
  document.addEventListener('click', function (e) {
    var t = e.target;
    // header cart icon (homepage theme button / standalone pages)
    var opener = t.closest('[data-testid="cart-drawer-trigger"],[data-cart-open]');
    if (opener) { e.preventDefault(); open(); return; }
    // homepage product cards: "Add" (single variant) and "Choose" (has options -> product page)
    var add = t.closest('.quick-add__button--add');
    if (add) {
      e.preventDefault(); e.stopPropagation();
      var form = add.closest('form'), vid = form && form.querySelector('input[name="id"]');
      var qty = form && form.querySelector('input[name="quantity"]');
      if (vid && Cart.add(vid.value, qty ? qty.value : 1)) {
        add.setAttribute('data-added', 'true'); setTimeout(function () { add.removeAttribute('data-added'); }, 1500); // theme's "added" checkmark
        open();
      }
      else toast('Sorry, this item is sold out');
      return;
    }
    var choose = t.closest('.quick-add__button--choose');
    if (choose) {
      e.preventDefault(); e.stopPropagation();
      var qa = choose.closest('quick-add-component'), p = qa && CAT.products[qa.getAttribute('data-product-id')];
      if (p) location.href = BASE + 'products/' + p.handle + '.html';
    }
  }, true);

  // touch / small screens: the theme hides quick-add buttons unless the card has [stay-visible]
  var mq = window.matchMedia('(max-width: 749px), (hover: none)');
  var qaVisible = function () { document.querySelectorAll('quick-add-component.quick-add').forEach(function (q) { q.toggleAttribute('stay-visible', mq.matches); }); };
  qaVisible(); (mq.addEventListener ? mq.addEventListener('change', qaVisible) : mq.addListener(qaVisible));

  // product pages: variant pills, quantity stepper, add to cart
  document.querySelectorAll('[data-add-form]').forEach(function (form) {
    var qty = form.querySelector('input[name="quantity"]');
    var img = document.querySelector('[data-variant-image]'), price = document.querySelector('[data-variant-price]');
    var current = function () { var r = form.querySelector('input[name="variant"]:checked') || form.querySelector('input[name="variant"]'); return r && r.value; };
    var sync = function () {
      var v = CAT.variants[current()]; if (!v) return;
      if (price) price.textContent = fmt(v.price);
      if (img && v.image) img.src = BASE + v.image;
      var btn = form.querySelector('.tp-add'); btn.disabled = !v.available; btn.textContent = v.available ? 'Add to cart' : 'Sold out';
      var bn = form.querySelector('[data-buy-now]');
      if (bn) {
        var link = !CFG.CHECKOUT_URL && PL && v.available && PL[v.id];
        bn.hidden = !link;
        if (link) {
          bn.querySelector('[data-buy-now-link]').href = link;
          bn.querySelector('[data-test-note]').textContent = 'Opens secure Stripe checkout for this item.' + testNote();
        }
      }
    };
    form.addEventListener('change', function (e) { if (e.target.name === 'variant') sync(); if (e.target === qty) qty.value = clamp(qty.value); });
    form.addEventListener('click', function (e) {
      var s = e.target.closest('[data-step]'); if (!s) return;
      qty.value = clamp(Number(qty.value) + Number(s.getAttribute('data-step')));
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      qty.value = clamp(qty.value);
      if (Cart.add(current(), qty.value)) { open(); }
    });
    sync();
  });

  // success page clears the cart
  if (document.querySelector('[data-checkout-success]')) Cart.clear();

  /* ---------- checkout ---------- */
  var busy = false;
  function testNote() { return PLMODE === 'test' ? ' (Stripe test mode: no real charge. Use card 4242 4242 4242 4242.)' : ''; }
  // interim Payment Links can only pay for one product at a time: list one link per cart line
  function showLinks(ls) {
    var m = $('[data-tc-msg]');
    m.innerHTML = '<span>Each item is paid separately for now:</span>' + ls.map(function (l) {
      var v = CAT.variants[l.variant_id];
      return PL[l.variant_id] ? '<a class="tc-paylink" href="' + esc(PL[l.variant_id]) + '">Pay for ' + esc(v.title + (v.variant_title ? ' – ' + v.variant_title : '')) + ' × ' + l.quantity + '</a>' : '';
    }).join('') + (PLMODE === 'test' ? '<small>Stripe test mode: no real charge. Use card 4242 4242 4242 4242.</small>' : '');
    m.hidden = false;
  }
  function checkout() {
    if (busy || !lines().length) return;
    var url = (CFG.CHECKOUT_URL || '').trim();
    if (!url) {
      var ls = lines();
      if (PL) {
        if (ls.length === 1 && PL[ls[0].variant_id]) {
          var only = CAT.variants[ls[0].variant_id];
          if (ls[0].quantity > 1) {
            msg('Opening secure Stripe checkout. Please set the quantity to ' + ls[0].quantity + ' on the next page.' + testNote());
            setTimeout(function () { location.href = PL[ls[0].variant_id]; }, 1600);
          } else { location.href = PL[ls[0].variant_id]; }
          return;
        }
        showLinks(ls); return;
      }
      msg('Payments are coming soon. Online checkout isn\'t open yet, but your cart is saved on this device.'); return;
    }
    var btn = $('[data-tc-checkout]');
    busy = true; btn.disabled = true; btn.textContent = 'Redirecting…'; msg('');
    var items = lines().map(function (l) { return { product_id: CAT.variants[l.variant_id].product_id, variant_id: l.variant_id, quantity: l.quantity }; });
    fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ items: items }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok || !d.url) throw new Error(d.error || 'Checkout failed'); return d; }); })
      .then(function (d) { location.href = d.url; })
      .catch(function (err) {
        msg('Sorry, we couldn\'t start checkout (' + err.message + '). Please try again in a moment.');
        busy = false; btn.disabled = false; btn.textContent = 'Checkout';
      });
  }
  Cart.checkout = checkout;

  // keep tabs in sync
  window.addEventListener('storage', function (e) { if (e.key === KEY) { memory = null; render(); } });
  window.addEventListener('pageshow', function () { memory = null; render(); }); // bfcache
  render();
})();
