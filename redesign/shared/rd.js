/* Shared behaviour for the TRESORA redesign concepts (front-end only).
   Cart: the site's real cart (assets/js/cart.js → window.TresoraCart + drawer), shared across all pages.
   Account + newsletter: UI previews only. Nothing is sent or stored until a backend exists. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var doc = document.documentElement;
  var CAT = window.TRESORA_CATALOG || { products: {}, variants: {} };
  var BASE = doc.getAttribute('data-base') || '';
  var ROOT = doc.getAttribute('data-rd-root') || BASE;
  var Cart = window.TresoraCart;
  var params = new URLSearchParams(location.search);
  var emailOk = function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v).trim()); };
  var money = function (c) { return '$' + (c / 100).toFixed(2); };
  var esc = function (s) { return String(s).replace(/[&<>"']/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]; }); };
  var purl = function (h) { return ROOT + 'products/' + h + '.html'; };
  var LEADS = window.RD_LEADS || {};   // product-first photos (the items, not the packaging) per variant: [large, thumb]
  var leadImg = function (vid, small) { var l = LEADS[String(vid)]; return l ? l[small ? 1 : 0] : null; };
  var openCart = function () { if (Cart && Cart.open) Cart.open(); };

  /* ---- buying: cards and product pages share [data-rd-buy] ---- */
  function chosen(box) {
    var sel = $('[data-rd-variant]', box); if (sel) return sel.value;
    var r = $('input[name=variant]:checked', box); if (r) return r.value;
    var b = $('[data-rd-add]', box); return b && b.getAttribute('data-rd-add');
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-rd-add]');
    if (!b || b.disabled) return;
    e.preventDefault();
    var box = b.closest('[data-rd-buy]') || document, q = $('[data-rd-qty]', box);
    var qty = q ? Math.max(1, Math.min(10, parseInt(q.value, 10) || 1)) : 1;
    if (Cart && Cart.add(chosen(box), qty)) {
      b.classList.add('is-added'); var t = b.textContent; b.textContent = 'Added';
      setTimeout(function () { b.classList.remove('is-added'); b.textContent = t; }, 1400);
      openCart();
    }
  });
  function showVariant(box, o) {
    var img = $('[data-rd-img]', box), pr = $('[data-rd-price]', box), lab = $('[data-rd-optlabel]', box);
    if (img && o.getAttribute('data-img')) img.src = o.getAttribute('data-img');
    if (pr) pr.textContent = o.getAttribute('data-price');
    if (lab) lab.textContent = o.getAttribute('data-label');
    $$('[data-rd-thumb]', box).forEach(function (t) { t.removeAttribute('aria-current'); });
  }
  $$('[data-rd-variant]').forEach(function (sel) { sel.addEventListener('change', function () { showVariant(sel.closest('[data-rd-buy]'), sel.selectedOptions[0]); }); });
  $$('input[name=variant]').forEach(function (r) { r.addEventListener('change', function () { showVariant(r.closest('[data-rd-buy]'), r); }); });
  $$('[data-rd-thumb]').forEach(function (t) {
    t.addEventListener('click', function () {
      var m = $('[data-rd-main]'); if (m) m.src = t.getAttribute('data-rd-thumb');
      $$('[data-rd-thumb]').forEach(function (x) { x.removeAttribute('aria-current'); }); t.setAttribute('aria-current', 'true');
    });
  });
  $$('[data-rd-step]').forEach(function (s) {
    s.addEventListener('click', function () {
      var q = $('[data-rd-qty]', s.closest('.rd-qty')); q.value = Math.max(1, Math.min(10, (parseInt(q.value, 10) || 1) + Number(s.getAttribute('data-rd-step'))));
    });
  });

  /* ---- category filter, stock filter, sort and search over the real catalog ---- */
  var gridEl = $('[data-rd-grid]'), cards = $$('.rd-card', gridEl || document.createElement('div'));
  var tabs = $$('[data-rd-filter]'), result = $('[data-rd-result]'), none = $('[data-rd-noresult]');
  var sortEl = $('[data-rd-sort]'), stockEl = $('[data-rd-instock]'), titleEl = $('[data-rd-shoptitle]');
  var NAMES = { all: 'All gifts', art: 'Inspired by Art', city: 'Inspired by City', home: 'Atelier Home' };
  var state = { cat: 'all', q: '' };
  if (params.get('cat') && NAMES[params.get('cat')]) state.cat = params.get('cat');
  if (params.get('q')) state.q = params.get('q');
  function apply() {
    if (!gridEl) return;
    var n = 0, q = state.q.trim().toLowerCase(), stock = stockEl && stockEl.checked;
    cards.forEach(function (c) {
      var ok = (state.cat === 'all' || c.getAttribute('data-cat') === state.cat) && (!q || c.getAttribute('data-title').indexOf(q) > -1) && (!stock || c.getAttribute('data-avail') === '1');
      c.hidden = !ok; if (ok) n++;
    });
    if (sortEl) {
      var k = sortEl.value, val = function (c, a) { return a === 't' ? c.getAttribute('data-title') : Number(c.getAttribute(a === 'p' ? 'data-price' : 'data-order')); };
      cards.slice().sort(function (a, b) {
        if (k === 'price-asc') return val(a, 'p') - val(b, 'p') || val(a, 'o') - val(b, 'o');
        if (k === 'price-desc') return val(b, 'p') - val(a, 'p') || val(a, 'o') - val(b, 'o');
        if (k === 'az') return val(a, 't') < val(b, 't') ? -1 : 1;
        return val(a, 'o') - val(b, 'o');
      }).forEach(function (c) { gridEl.appendChild(c); });
    }
    tabs.forEach(function (t) { t.setAttribute('aria-pressed', String(t.getAttribute('data-rd-filter') === state.cat)); });
    if (result) result.textContent = n + ' product' + (n === 1 ? '' : 's') + (q ? ' for “' + state.q.trim() + '”' : '');
    if (none) none.hidden = n > 0;
    if (titleEl) titleEl.textContent = q ? 'Search results' : NAMES[state.cat];
    var qi0 = $('[data-rd-q]'); if (qi0 && document.activeElement !== qi0) qi0.value = state.q;
  }
  function syncUrl() {
    if (!sortEl || !history.replaceState) return;
    var u = new URLSearchParams(); if (state.cat !== 'all') u.set('cat', state.cat); if (state.q) u.set('q', state.q);
    history.replaceState(null, '', location.pathname + (u.toString() ? '?' + u : ''));
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { state.cat = t.getAttribute('data-rd-filter'); apply(); syncUrl(); }); });
  if (sortEl) sortEl.addEventListener('change', apply);
  if (stockEl) stockEl.addEventListener('change', apply);
  var clear = $('[data-rd-clear]'); if (clear) clear.addEventListener('click', function () { state.cat = 'all'; state.q = ''; if (stockEl) stockEl.checked = false; apply(); syncUrl(); });

  var form = $('[data-rd-search]'), qi = $('[data-rd-q]'), sug = $('[data-rd-suggest]');
  var products = Object.keys(CAT.products).map(function (k) { return CAT.products[k]; });
  function suggest() {
    var q = qi.value.trim().toLowerCase();
    if (!q) { sug.hidden = true; qi.setAttribute('aria-expanded', 'false'); return; }
    var hits = products.filter(function (p) { return p.title.toLowerCase().indexOf(q) > -1 || p.handle.indexOf(q.replace(/\s+/g, '-')) > -1; }).slice(0, 6);
    sug.innerHTML = hits.length ? hits.map(function (p) {
      var v = CAT.variants[p.variants[0]];
      return '<a role="option" href="' + purl(p.handle) + '"><img src="' + (leadImg(v.id, true) || BASE + v.thumb) + '" alt="" width="44" height="44"><span>' +
        esc(p.title) + '</span><b>' + money(v.price) + '</b></a>';
    }).join('') + '<button type="button" data-rd-all>See all results</button>' : '<p>No matches. Try “Paris”, “Klimt” or “bottle”.</p>';
    sug.hidden = false; qi.setAttribute('aria-expanded', 'true');
  }
  function showAll() {
    var q = qi.value.trim();
    if (!gridEl) { location.href = ROOT + 'shop.html' + (q ? '?q=' + encodeURIComponent(q) : ''); return; }
    state.q = q; state.cat = 'all'; apply(); syncUrl(); sug.hidden = true; doc.classList.remove('rd-searching');
    var shop = $('#shop'); if (shop) shop.scrollIntoView({ behavior: 'smooth' });
  }
  if (form) {
    qi.addEventListener('input', suggest);
    qi.addEventListener('focus', suggest);
    form.addEventListener('submit', function (e) { e.preventDefault(); showAll(); });
    sug.addEventListener('click', function (e) { if (e.target.closest('[data-rd-all]')) showAll(); });
    document.addEventListener('click', function (e) { if (!form.contains(e.target)) { sug.hidden = true; qi.setAttribute('aria-expanded', 'false'); } });
    qi.addEventListener('keydown', function (e) { if (e.key === 'Escape') { sug.hidden = true; qi.blur(); } });
  }
  var st = $('[data-rd-searchtoggle]');
  if (st) st.addEventListener('click', function () { doc.classList.toggle('rd-searching'); if (doc.classList.contains('rd-searching')) qi.focus(); });

  /* ---- mobile menu ---- */
  var mb = $('[data-rd-menu]');
  function closeMenu() { doc.classList.remove('rd-menu-open'); if (mb) mb.setAttribute('aria-expanded', 'false'); }
  if (mb) mb.addEventListener('click', function () { var o = doc.classList.toggle('rd-menu-open'); mb.setAttribute('aria-expanded', String(o)); });
  $$('.rd-nav a').forEach(function (a) { a.addEventListener('click', closeMenu); });

  /* ---- open panels (mobile menu, mobile search, cart drawer): close on outside tap / backdrop, Escape, and browser back ---- */
  var PANELS = {
    menu: { on: function () { return doc.classList.contains('rd-menu-open'); }, close: closeMenu, inside: ['.rd-nav', '[data-rd-menu]'] },
    search: { on: function () { return doc.classList.contains('rd-searching'); }, close: function () { doc.classList.remove('rd-searching'); if (sug) sug.hidden = true; },
              inside: ['[data-rd-search]', '[data-rd-searchtoggle]', '[data-rd-suggest]'] },
    cart: { on: function () { return doc.classList.contains('tc-open'); }, close: function () { if (window.TresoraCart) window.TresoraCart.close(); }, inside: ['.tc-drawer'] }
  };
  var bd = document.createElement('div'); bd.className = 'rd-backdrop'; bd.setAttribute('aria-hidden', 'true'); document.body.appendChild(bd);
  var openNames = function () { return Object.keys(PANELS).filter(function (k) { return PANELS[k].on(); }); };
  var closePanel = function (k) { if (PANELS[k].on()) PANELS[k].close(); };
  bd.addEventListener('click', function () { closePanel('menu'); closePanel('search'); });
  // a tap anywhere outside an open menu / search closes it (the cart drawer has its own full-screen overlay)
  // (pointerup as well as click: iOS Safari fires no click for taps on non-interactive areas)
  var outside = function (e) {
    ['menu', 'search'].forEach(function (k) {
      if (!PANELS[k].on()) return;
      var inside = PANELS[k].inside.some(function (sel) { var el = e.target.closest && e.target.closest(sel); return !!el; });
      if (!inside) PANELS[k].close();
    });
  };
  document.addEventListener('pointerup', outside, true);
  var ov = document.querySelector('.tc-overlay');
  if (ov) ov.addEventListener('pointerup', function () { PANELS.cart.close(); });
  document.addEventListener('click', outside, true);
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var o = openNames(); if (!o.length) return;
    o.forEach(closePanel); if (mb && o.indexOf('menu') > -1) mb.focus();
  });
  // browser back (mobile back gesture) closes the panel instead of leaving the page
  var hist = {}, ignorePop = 0, leaving = false;
  // never call history.back() while the page is navigating away (a link inside a panel, the Stripe checkout redirect)
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (a && !e.defaultPrevented && a.getAttribute('href').charAt(0) !== '#' && a.target !== '_blank') leaving = true;
  });
  window.addEventListener('beforeunload', function () { leaving = true; });
  window.addEventListener('pageshow', function () { leaving = false; });
  var sync = function () {
    Object.keys(PANELS).forEach(function (k) {
      var on = PANELS[k].on();
      if (on && !hist[k]) { hist[k] = true; try { history.pushState({ rdPanel: k }, ''); } catch (err) {} }
      else if (!on && hist[k]) {
        hist[k] = false;
        setTimeout(function () { if (!leaving && history.state && history.state.rdPanel === k) { ignorePop++; history.back(); } }, 60);
      }
    });
    doc.classList.toggle('rd-has-backdrop', PANELS.menu.on() || PANELS.search.on());
  };
  window.addEventListener('popstate', function () {
    if (ignorePop) { ignorePop--; return; }
    Object.keys(PANELS).forEach(function (k) { if (hist[k] && !(history.state && history.state.rdPanel === k)) { hist[k] = false; closePanel(k); } });
    sync();
  });
  new MutationObserver(sync).observe(doc, { attributes: true, attributeFilter: ['class'] });

  /* ---- header state on scroll ---- */
  var hd = $('[data-rd-header]');
  var onScroll = function () { hd.classList.toggle('is-scrolled', window.scrollY > 10); };
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* ---- cart drawer: keep links inside this concept + add a link to the full cart page ---- */
  var items = $('.tc-items');
  function fixDrawer() {
    $$('.tc-items a[href]').forEach(function (a) {
      var m = a.getAttribute('href').match(/products\/([a-z0-9-]+)\.html$/);
      if (m && a.getAttribute('href') !== purl(m[1])) a.setAttribute('href', purl(m[1]));
    });
    $$('.tc-item').forEach(function (li) {
      var img = $('img', li), src = leadImg(li.getAttribute('data-variant'), true);
      if (img && src && img.getAttribute('src') !== src) img.setAttribute('src', src);
    });
  }
  if (items) { new MutationObserver(fixDrawer).observe(items, { childList: true, subtree: true }); fixDrawer(); }
  var foot = $('[data-tc-foot]');
  if (foot && !$('.rd-drawer-cartlink')) { var a = document.createElement('a'); a.className = 'rd-drawer-cartlink'; a.href = ROOT + 'cart.html'; a.textContent = 'View full cart'; foot.appendChild(a); }

  /* ---- cart page ---- */
  var cp = $('[data-rd-cartpage]');
  function renderCart() {
    if (!cp || !Cart) return;
    var ls = Cart.items(), list = $('[data-rd-cartlines]');
    list.innerHTML = ls.map(function (l) {
      var v = CAT.variants[l.variant_id];
      return '<li class="rd-line" data-variant="' + v.id + '"><a class="rd-line__img" href="' + purl(v.handle) + '"><img src="' + (leadImg(v.id) || BASE + esc(v.image)) + '" alt="" width="160" height="120"></a>' +
        '<div class="rd-line__info"><a href="' + purl(v.handle) + '">' + esc(v.title) + '</a>' + (v.variant_title ? '<span>' + esc(v.variant_title) + '</span>' : '') + '<span>' + money(v.price) + '</span></div>' +
        '<div class="rd-qty"><button type="button" data-rd-dec aria-label="Decrease quantity"' + (l.quantity <= 1 ? ' disabled' : '') + '>−</button><output>' + l.quantity + '</output><button type="button" data-rd-inc aria-label="Increase quantity"' + (l.quantity >= 10 ? ' disabled' : '') + '>+</button></div>' +
        '<div class="rd-line__total"><b>' + money(v.price * l.quantity) + '</b><button type="button" class="rd-linkbtn" data-rd-remove>Remove</button></div></li>';
    }).join('');
    $('[data-rd-cartempty]').hidden = ls.length > 0;
    $('.rd-cartpage__cols').hidden = !ls.length;
    $('[data-rd-summary]').hidden = !ls.length;
    $('[data-rd-subtotal]').textContent = money(Cart.subtotal());
  }
  if (cp && Cart) {
    ['add', 'set', 'remove', 'clear'].forEach(function (k) { var f = Cart[k]; Cart[k] = function () { var r = f.apply(Cart, arguments); setTimeout(renderCart, 0); return r; }; });
    window.addEventListener('storage', function () { setTimeout(renderCart, 0); });
    window.addEventListener('pageshow', function () { setTimeout(renderCart, 0); });
    cp.addEventListener('click', function (e) {
      var li = e.target.closest('.rd-line'); if (!li) return;
      var id = Number(li.getAttribute('data-variant')), line = Cart.items().filter(function (l) { return l.variant_id === id; })[0]; if (!line) return;
      if (e.target.closest('[data-rd-inc]')) Cart.set(id, line.quantity + 1);
      else if (e.target.closest('[data-rd-dec]')) Cart.set(id, line.quantity - 1);
      else if (e.target.closest('[data-rd-remove]')) Cart.remove(id);
    });
    $('[data-rd-checkout]').addEventListener('click', function () {
      $('[data-rd-cartmsg]').textContent = 'Opening secure checkout…';
      openCart(); if (Cart.checkout) Cart.checkout();
    });
    renderCart();
  }

  /* ---- account page (UI only) ---- */
  var ap = $('[data-rd-accountpage]'), auth = $('[data-rd-auth]');
  if (ap && auth) {
    var mode = function (m) {
      ap.setAttribute('data-mode', m);
      $$('[data-rd-tab]', ap).forEach(function (t) { t.setAttribute('aria-selected', String(t.getAttribute('data-rd-tab') === m)); });
      $('[data-rd-modal-title]', ap).textContent = m === 'signup' ? 'Create your account' : 'Welcome back';
      $('[data-rd-submit]', ap).textContent = m === 'signup' ? 'Create account' : 'Sign in';
      auth.password.setAttribute('autocomplete', m === 'signup' ? 'new-password' : 'current-password');
      $('[data-rd-msg]', auth).textContent = '';
    };
    mode(params.get('mode') === 'signup' ? 'signup' : 'signin');
    $$('[data-rd-tab]', ap).forEach(function (t) { t.addEventListener('click', function () { mode(t.getAttribute('data-rd-tab')); }); });
    $('[data-rd-showpass]', ap).addEventListener('click', function (e) {
      var p = auth.password, show = p.type === 'password'; p.type = show ? 'text' : 'password'; e.target.textContent = show ? 'Hide' : 'Show';
    });
    $('[data-rd-forgot]', ap).addEventListener('click', function () {
      var m = $('[data-rd-msg]', auth);
      m.textContent = emailOk(auth.email.value) ? 'Preview: a reset link would be emailed to ' + auth.email.value.trim() + '.' : 'Enter your email first.';
    });
    auth.addEventListener('submit', function (e) {
      e.preventDefault();
      var m = $('[data-rd-msg]', auth), signup = ap.getAttribute('data-mode') === 'signup';
      m.className = 'rd-auth__msg is-error';
      if (!emailOk(auth.email.value)) { m.textContent = 'Please enter a valid email address.'; auth.email.focus(); return; }
      if (auth.password.value.length < 8) { m.textContent = 'Password must be at least 8 characters.'; auth.password.focus(); return; }
      m.className = 'rd-auth__msg is-ok';
      m.textContent = signup ? 'Looks good! Accounts launch soon. This preview did not create an account.' : 'Accounts launch soon. This preview did not sign you in.';
      auth.password.value = '';
    });
  }

  /* ---- newsletter (UI only) ---- */
  $$('[data-rd-news]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var m = $('[data-rd-msg]', f);
      m.className = 'rd-news__msg is-error';
      if (!emailOk(f.email.value)) { m.textContent = 'Please enter a valid email address.'; return; }
      if (!f.consent.checked) { m.textContent = 'Please confirm you agree to receive emails.'; return; }
      m.className = 'rd-news__msg is-ok';
      m.textContent = 'Thank you! (Preview: sign-up will connect to the mailing list at launch.)';
      f.reset();
    });
  });
  /* ---- full-screen city slideshow (v4): crossfade + slow zoom, ~5 s per slide, progress bars, swipe, pause on hover ---- */
  var ss = $('[data-rd-slides]');
  if (ss) {
    var slides = $$('[data-rd-slide]', ss), dots = $$('[data-rd-dot]', ss), pauseBtn = $('[data-rd-pause]', ss);
    var DUR = 5000, cur = 0, timer = null, started = 0, remain = DUR, hoverPaused = false, userPaused = false;
    var show = function (n) {
      n = (n + slides.length) % slides.length;
      slides.forEach(function (sl, i) {
        var on = i === n; sl.classList.toggle('is-active', on); sl.setAttribute('aria-hidden', String(!on));
        var a = $('a', sl); if (a) a.tabIndex = on ? 0 : -1;
      });
      dots.forEach(function (d, i) { d.removeAttribute('aria-current'); d.classList.toggle('is-done', i < n); });
      void ss.offsetWidth;   // restart the progress animation
      dots[n].setAttribute('aria-current', 'true');
      cur = n; ss.setAttribute('data-rd-current', String(n)); remain = DUR; schedule();
    };
    var schedule = function () {
      clearTimeout(timer); timer = null;
      if (hoverPaused || userPaused || document.hidden) return;
      started = Date.now(); timer = setTimeout(function () { show(cur + 1); }, remain);
    };
    var pause = function () { if (timer) { remain = Math.max(0, remain - (Date.now() - started)); clearTimeout(timer); timer = null; } ss.classList.add('is-paused'); };
    var resume = function () { if (hoverPaused || userPaused || document.hidden) return; ss.classList.remove('is-paused'); schedule(); };
    dots.forEach(function (d, i) { d.addEventListener('click', function () { show(i); }); });
    if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
      // pause while the pointer is on the caption / controls (the whole screen is the slideshow, so hovering anywhere would stop it for good)
      $$('.rd-slide__text, .rd-slides__nav, .rd-slides__pause', ss).forEach(function (el) {
        el.addEventListener('mouseenter', function () { hoverPaused = true; pause(); });
        el.addEventListener('mouseleave', function () { hoverPaused = false; resume(); });
      });
    }
    if (pauseBtn) pauseBtn.addEventListener('click', function () {
      userPaused = !userPaused; pauseBtn.setAttribute('aria-pressed', String(userPaused));
      pauseBtn.setAttribute('aria-label', userPaused ? 'Play slideshow' : 'Pause slideshow');
      if (userPaused) pause(); else resume();
    });
    document.addEventListener('visibilitychange', function () { if (document.hidden) pause(); else resume(); });
    ss.addEventListener('focusin', function () { hoverPaused = true; pause(); });
    ss.addEventListener('focusout', function () { hoverPaused = false; resume(); });
    // swipe (touch + pen + mouse drag) via pointer events; vertical scrolling stays native (touch-action: pan-y)
    var sx = null, sy = 0;
    ss.addEventListener('pointerdown', function (e) { if (e.target.closest('a,button')) return; sx = e.clientX; sy = e.clientY; });
    ss.addEventListener('pointerup', function (e) {
      if (sx === null) return; var dx = e.clientX - sx, dy = e.clientY - sy; sx = null;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) show(cur + (dx < 0 ? 1 : -1));
    });
    ss.addEventListener('pointercancel', function () { sx = null; });
    ss.addEventListener('keydown', function (e) { if (e.key === 'ArrowRight') show(cur + 1); if (e.key === 'ArrowLeft') show(cur - 1); });
    show(0);
  }
  apply();
})();
