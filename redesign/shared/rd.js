/* Shared behaviour for the TRESORA redesign concepts (front-end only).
   Cart: uses the site's real cart (assets/js/cart.js → window.TresoraCart + drawer).
   Account + newsletter: UI previews only. Nothing is sent or stored until a backend exists. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var CAT = window.TRESORA_CATALOG || { products: {}, variants: {} };
  var BASE = document.documentElement.getAttribute('data-base') || '';
  var emailOk = function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v).trim()); };

  /* ---- add to cart ---- */
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-rd-add]');
    if (!b || b.disabled) return;
    e.preventDefault();
    var sel = b.closest('.rd-card').querySelector('[data-rd-variant]');
    var id = sel ? sel.value : b.getAttribute('data-rd-add');
    if (window.TresoraCart && window.TresoraCart.add(id, 1)) {
      b.classList.add('is-added'); var t = b.textContent; b.textContent = 'Added ✓';
      setTimeout(function () { b.classList.remove('is-added'); b.textContent = t; }, 1400);
      var opener = $('[data-cart-open]'); if (opener) opener.click();
    }
  });
  $$('[data-rd-variant]').forEach(function (sel) {
    sel.addEventListener('change', function () {
      var o = sel.selectedOptions[0], card = sel.closest('.rd-card');
      card.querySelector('[data-rd-img]').src = o.getAttribute('data-img');
      card.querySelector('[data-rd-price]').textContent = o.getAttribute('data-price');
    });
  });

  /* ---- category filter + search over the real catalog ---- */
  var cards = $$('.rd-card'), tabs = $$('[data-rd-filter]'), result = $('[data-rd-result]'), none = $('[data-rd-noresult]');
  var state = { cat: 'all', q: '' };
  function apply() {
    var n = 0, q = state.q.trim().toLowerCase();
    cards.forEach(function (c) {
      var ok = (state.cat === 'all' || c.getAttribute('data-cat') === state.cat) && (!q || c.getAttribute('data-title').indexOf(q) > -1);
      c.hidden = !ok; if (ok) n++;
    });
    tabs.forEach(function (t) { t.setAttribute('aria-pressed', String(t.getAttribute('data-rd-filter') === state.cat)); });
    if (result) result.textContent = n + ' product' + (n === 1 ? '' : 's') + (q ? ' for “' + state.q.trim() + '”' : '');
    if (none) none.hidden = n > 0;
  }
  tabs.forEach(function (t) { t.addEventListener('click', function () { state.cat = t.getAttribute('data-rd-filter'); apply(); }); });
  $$('[data-rd-goto]').forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault(); state.cat = a.getAttribute('data-rd-goto'); state.q = ''; var qi = $('[data-rd-q]'); if (qi) qi.value = '';
      apply(); closeMenu(); var shop = $('#shop'); if (shop) shop.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  var clear = $('[data-rd-clear]'); if (clear) clear.addEventListener('click', function () { state.cat = 'all'; state.q = ''; $('[data-rd-q]').value = ''; apply(); });

  var form = $('[data-rd-search]'), qi = $('[data-rd-q]'), sug = $('[data-rd-suggest]');
  var products = Object.keys(CAT.products).map(function (k) { return CAT.products[k]; });
  var money = function (c) { return '$' + (c / 100).toFixed(2); };
  function suggest() {
    var q = qi.value.trim().toLowerCase();
    if (!q) { sug.hidden = true; qi.setAttribute('aria-expanded', 'false'); return; }
    var hits = products.filter(function (p) { return p.title.toLowerCase().indexOf(q) > -1 || p.handle.indexOf(q.replace(/\s+/g, '-')) > -1; }).slice(0, 6);
    sug.innerHTML = hits.length ? hits.map(function (p) {
      var v = CAT.variants[p.variants[0]];
      return '<a role="option" href="' + BASE + 'products/' + p.handle + '.html"><img src="' + BASE + v.thumb + '" alt="" width="44" height="44"><span>' +
        p.title.replace(/[<>&]/g, '') + '</span><b>' + money(v.price) + '</b></a>';
    }).join('') + '<button type="button" data-rd-all>See all results</button>' : '<p>No matches. Try “Paris”, “Klimt” or “bottle”.</p>';
    sug.hidden = false; qi.setAttribute('aria-expanded', 'true');
  }
  if (form) {
    qi.addEventListener('input', suggest);
    qi.addEventListener('focus', suggest);
    form.addEventListener('submit', function (e) { e.preventDefault(); showAll(); });
    sug.addEventListener('click', function (e) { if (e.target.closest('[data-rd-all]')) showAll(); });
    document.addEventListener('click', function (e) { if (!form.contains(e.target)) { sug.hidden = true; qi.setAttribute('aria-expanded', 'false'); } });
    qi.addEventListener('keydown', function (e) { if (e.key === 'Escape') { sug.hidden = true; qi.blur(); } });
  }
  function showAll() { state.q = qi.value; state.cat = 'all'; apply(); sug.hidden = true; document.documentElement.classList.remove('rd-searching'); $('#shop').scrollIntoView({ behavior: 'smooth' }); }
  var st = $('[data-rd-searchtoggle]');
  if (st) st.addEventListener('click', function () { document.documentElement.classList.toggle('rd-searching'); if (document.documentElement.classList.contains('rd-searching')) qi.focus(); });

  /* ---- mobile menu ---- */
  var mb = $('[data-rd-menu]');
  function closeMenu() { document.documentElement.classList.remove('rd-menu-open'); if (mb) mb.setAttribute('aria-expanded', 'false'); }
  if (mb) mb.addEventListener('click', function () { var o = document.documentElement.classList.toggle('rd-menu-open'); mb.setAttribute('aria-expanded', String(o)); });
  $$('.rd-nav a').forEach(function (a) { a.addEventListener('click', closeMenu); });

  /* ---- header shadow on scroll ---- */
  var hd = $('[data-rd-header]');
  var onScroll = function () { hd.classList.toggle('is-scrolled', window.scrollY > 10); };
  window.addEventListener('scroll', onScroll, { passive: true }); onScroll();

  /* ---- account modal (UI only) ---- */
  var modal = $('[data-rd-modal]'), auth = $('[data-rd-auth]');
  function mode(m) {
    modal.setAttribute('data-mode', m);
    $$('[data-rd-tab]', modal).forEach(function (t) { t.setAttribute('aria-selected', String(t.getAttribute('data-rd-tab') === m)); });
    $('[data-rd-modal-title]', modal).textContent = m === 'signup' ? 'Create your account' : 'Welcome back';
    $('[data-rd-submit]', modal).textContent = m === 'signup' ? 'Create account' : 'Sign in';
    auth.password.setAttribute('autocomplete', m === 'signup' ? 'new-password' : 'current-password');
    $('[data-rd-msg]', auth).textContent = '';
  }
  $$('[data-rd-account]').forEach(function (b) {
    b.addEventListener('click', function () { mode(b.getAttribute('data-rd-account')); if (modal.showModal) modal.showModal(); else modal.setAttribute('open', ''); auth.email.focus(); });
  });
  $$('[data-rd-tab]', modal).forEach(function (t) { t.addEventListener('click', function () { mode(t.getAttribute('data-rd-tab')); }); });
  modal.addEventListener('click', function (e) { if (e.target === modal) modal.close(); });
  $('[data-rd-showpass]', modal).addEventListener('click', function (e) {
    var p = auth.password, show = p.type === 'password'; p.type = show ? 'text' : 'password'; e.target.textContent = show ? 'Hide' : 'Show';
  });
  $('[data-rd-forgot]', modal).addEventListener('click', function () {
    var m = $('[data-rd-msg]', auth);
    m.textContent = emailOk(auth.email.value) ? 'Preview: a reset link would be emailed to ' + auth.email.value.trim() + '.' : 'Enter your email first.';
  });
  auth.addEventListener('submit', function (e) {
    e.preventDefault();
    var m = $('[data-rd-msg]', auth), signup = modal.getAttribute('data-mode') === 'signup';
    m.className = 'rd-auth__msg is-error';
    if (!emailOk(auth.email.value)) { m.textContent = 'Please enter a valid email address.'; auth.email.focus(); return; }
    if (auth.password.value.length < 8) { m.textContent = 'Password must be at least 8 characters.'; auth.password.focus(); return; }
    m.className = 'rd-auth__msg is-ok';
    m.textContent = signup ? 'Looks good! Accounts launch soon. This preview did not create an account.' : 'Accounts launch soon. This preview did not sign you in.';
    auth.password.value = '';
  });

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
  apply();
})();
