/* TRESORA welcome popup: "Join with your email, get 15% off".
   - Shows ~1s after the first page load; not again for 30 days after it is closed or used (localStorage).
   - Never on checkout / thank-you pages. Test anytime with ?welcome=1.
   - Emails go to the Supabase table public.newsletter_signups (insert-only for the public key; nobody can read it from the site).
   - Turn off with TRESORA_CONFIG.WELCOME_POPUP = false (assets/js/config.js). Code shown: TRESORA_CONFIG.WELCOME_CODE.
   Spanish text comes from i18n/es.json via the site's language switcher. */
(function () {
  var CFG = window.TRESORA_CONFIG || {};
  var FORCE = /[?&]welcome=1\b/.test(location.search);
  if (CFG.WELCOME_POPUP === false && !FORCE) return;
  var CODE = CFG.WELCOME_CODE || 'WELCOME15';
  var SB_URL = 'https://bnequlkhwcnuzplsdktp.supabase.co', SB_KEY = 'sb_publishable_N9-HUpcVuEm5-3Aey6vMzg_jSeKivQ3'; // public by design
  var KEY = 'tresora-welcome', DAYS = 30, DELAY = 1000;
  var path = location.pathname.toLowerCase();
  if (/(^|\/)(success|cancel|cart|checkout|thank-you|thanks|account|reset-password)(\.html)?$/.test(path) || /[?&]session_id=/.test(location.search)) return;
  function seenRecently() { try { var t = +localStorage.getItem(KEY); return t && Date.now() - t < DAYS * 864e5; } catch (e) { return false; } }
  function remember() { try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {} }
  if (!FORCE && seenRecently()) return;

  var CSS = '.tw-back{position:fixed;inset:0;z-index:2147483600;background:rgba(10,20,15,.62);display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;transition:opacity .25s ease}' +
    '.tw-back.is-in{opacity:1}' +
    '.tw-box{position:relative;width:100%;max-width:440px;max-height:calc(100vh - 32px);overflow:auto;background:#1F3B2D;color:#F3EEE3;border:1px solid #C9A961;border-radius:4px;box-shadow:0 24px 60px rgba(0,0,0,.35);padding:40px 32px 28px;text-align:center;font-family:"GT Standard",system-ui,sans-serif;transform:translateY(12px);transition:transform .25s ease}' +
    '.tw-back.is-in .tw-box{transform:none}' +
    '.tw-box:before{content:"";position:absolute;inset:6px;border:1px solid rgba(201,169,97,.35);border-radius:2px;pointer-events:none}' +
    '.tw-x{position:absolute;top:10px;right:10px;width:40px;height:40px;border:0;background:none;color:#C9A961;font-size:26px;line-height:1;cursor:pointer;border-radius:50%;z-index:1}' +
    '.tw-x:hover{background:rgba(201,169,97,.12)}' +
    '.tw-eyebrow{margin:0 0 10px;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#C9A961}' +
    '.tw-h{margin:0 0 12px;font-family:"Cormorant",Georgia,serif;font-weight:500;font-size:34px;line-height:1.1;color:#F3EEE3}' +
    '.tw-h b{color:#C9A961;font-weight:600}' +
    '.tw-p{margin:0 0 22px;font-size:14px;line-height:1.55;color:#D8D3C6}' +
    '.tw-form{display:flex;flex-direction:column;gap:12px;text-align:left}' +
    '.tw-in{width:100%;box-sizing:border-box;height:48px;padding:0 14px;border:1px solid rgba(201,169,97,.6);border-radius:2px;background:rgba(255,255,255,.06);color:#F3EEE3;font:inherit;font-size:16px}' +
    '.tw-in::placeholder{color:#AFA998}.tw-in[aria-invalid=true]{border-color:#ffb4a8}' +
    '.tw-btn{height:48px;border:1px solid #C9A961;border-radius:2px;background:#C9A961;color:#1F3B2D;font:inherit;font-size:13px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;cursor:pointer}' +
    '.tw-btn:hover{background:#d6b974}.tw-btn[disabled]{opacity:.65;cursor:wait}' +
    '.tw-consent{display:flex;gap:10px;align-items:flex-start;font-size:12px;line-height:1.45;color:#CFC9BB;cursor:pointer}' +
    '.tw-consent input{margin:2px 0 0;width:16px;height:16px;accent-color:#C9A961;flex:none}' +
    '.tw-msg{min-height:18px;margin:0;font-size:13px;color:#ffb4a8}' +
    '.tw-no{margin-top:6px;border:0;background:none;color:#CFC9BB;font:inherit;font-size:12px;text-decoration:underline;cursor:pointer;align-self:center}' +
    '.tw-code{display:flex;align-items:stretch;justify-content:center;gap:0;margin:4px auto 14px;max-width:320px}' +
    '.tw-code span{flex:1;display:flex;align-items:center;justify-content:center;border:1px dashed #C9A961;border-right:0;font-size:22px;font-weight:600;letter-spacing:.18em;color:#F3EEE3;padding:10px 12px;user-select:all}' +
    '.tw-code .tw-btn{padding:0 18px;border-radius:0 2px 2px 0}' +
    '.tw-box :focus-visible{outline:2px solid #F3EEE3;outline-offset:2px}' +
    '.tw-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '@media(max-width:480px){.tw-back{align-items:flex-end;padding:0}.tw-box{max-width:none;border-radius:4px 4px 0 0;padding:36px 22px 24px}.tw-h{font-size:29px}}' +
    '@media(prefers-reduced-motion:reduce){.tw-back,.tw-box{transition:none}}';

  function h(tag, attrs, kids) {
    var e = document.createElement(tag);
    for (var k in attrs) { if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); }
    (kids || []).forEach(function (c) { e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    return e;
  }
  var lastFocus, back, box;
  function close() {
    if (!back) return; remember();
    document.removeEventListener('keydown', onKey, true);
    back.classList.remove('is-in'); var b = back; back = null;
    setTimeout(function () { b.remove(); document.documentElement.style.overflow = ''; }, 250);
    if (lastFocus && lastFocus.focus) try { lastFocus.focus(); } catch (e) {}
  }
  function focusables() { return [].slice.call(box.querySelectorAll('button,input,a[href]')).filter(function (e) { return !e.disabled && e.offsetParent !== null; }); }
  function onKey(e) {
    if (!back) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key === 'Tab') {
      var f = focusables(); if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  function track(name) { try { if (window.gtag) window.gtag('event', name, { method: 'welcome_popup' }); } catch (e) {} }

  function success(content) {
    remember(); track('generate_lead');
    content.innerHTML = '';
    var copy = h('button', { type: 'button', 'class': 'tw-btn', text: 'Copy' });
    var status = h('p', { 'class': 'tw-sr', role: 'status', 'aria-live': 'polite' });
    copy.addEventListener('click', function () {
      var done = function () { copy.textContent = 'Copied'; status.textContent = 'Code copied'; setTimeout(function () { copy.textContent = 'Copy'; }, 2000); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(CODE).then(done, fallback); else fallback();
      function fallback() { var t = h('textarea', {}); t.value = CODE; t.setAttribute('readonly', ''); t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); done(); } catch (e) {} t.remove(); }
    });
    var shop = h('button', { type: 'button', 'class': 'tw-no', text: 'Continue shopping' }); shop.addEventListener('click', close);
    content.appendChild(h('p', { 'class': 'tw-eyebrow', text: 'Welcome to TRESORA' }));
    content.appendChild(h('h2', { 'class': 'tw-h', id: 'tw-title', text: 'Your 15% welcome code' }));
    content.appendChild(h('div', { 'class': 'tw-code' }, [h('span', { 'data-lang-skip': '', text: CODE }), copy]));
    content.appendChild(h('p', { 'class': 'tw-p', text: 'Enter this code in the promotion code field at checkout.' }));
    content.appendChild(status);
    content.appendChild(shop);
    copy.focus();
  }

  function open() {
    if (back || (!FORCE && seenRecently())) return;
    if (!document.getElementById('tw-css')) document.head.appendChild(h('style', { id: 'tw-css', text: CSS }));
    lastFocus = document.activeElement;
    var x = h('button', { type: 'button', 'class': 'tw-x', 'aria-label': 'Close', text: '\u00d7' }); x.addEventListener('click', close);
    var email = h('input', { 'class': 'tw-in', id: 'tw-email', type: 'email', name: 'email', placeholder: 'Email address', autocomplete: 'email', required: '', maxlength: '254' });
    var consent = h('input', { type: 'checkbox', name: 'consent' });
    var msg = h('p', { 'class': 'tw-msg', role: 'alert', 'aria-live': 'assertive' });
    var btn = h('button', { type: 'submit', 'class': 'tw-btn', text: 'Get my 15% off' });
    var no = h('button', { type: 'button', 'class': 'tw-no', text: 'No thanks' }); no.addEventListener('click', close);
    var form = h('form', { 'class': 'tw-form', novalidate: '' }, [
      h('label', { 'class': 'tw-sr', 'for': 'tw-email', text: 'Email address' }), email,
      h('label', { 'class': 'tw-consent' }, [consent, h('span', { text: 'I agree to receive emails from TRESORA. Unsubscribe anytime.' })]),
      msg, btn, no]);
    var content = h('div', {}, [
      h('p', { 'class': 'tw-eyebrow', text: 'Welcome to TRESORA' }),
      h('h2', { 'class': 'tw-h', id: 'tw-title', text: 'Get 15% off your first order' }),
      h('p', { 'class': 'tw-p', text: 'Join the TRESORA list for new collections and early access, and get your welcome code right away.' }),
      form]);
    box = h('div', { 'class': 'tw-box', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'tw-title' }, [x, content]);
    back = h('div', { 'class': 'tw-back', 'data-tresora-welcome': '' }, [box]);
    back.addEventListener('mousedown', function (e) { if (e.target === back) close(); });
    form.addEventListener('submit', function (e) {
      e.preventDefault(); msg.textContent = ''; email.removeAttribute('aria-invalid');
      var v = (email.value || '').trim();
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(v) || v.length > 254) { msg.textContent = 'Please enter a valid email address.'; email.setAttribute('aria-invalid', 'true'); email.focus(); return; }
      if (!consent.checked) { msg.textContent = 'Please tick the box to agree to receive emails.'; consent.focus(); return; }
      btn.disabled = true; btn.textContent = 'Sending…';
      var lang = 'en'; try { lang = localStorage.getItem('tresora-lang') === 'es' ? 'es' : 'en'; } catch (er) {}
      fetch(SB_URL + '/rest/v1/newsletter_signups', {
        method: 'POST',
        headers: { apikey: SB_KEY, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
        body: JSON.stringify({ email: v.toLowerCase(), consent: true, source: 'welcome_popup', lang: lang, page: location.pathname.slice(0, 300) })
      }).then(function (r) {
        if (r.ok || r.status === 409) success(content); // 409 = already on the list: still show the code
        else throw new Error('HTTP ' + r.status);
      }).catch(function () {
        btn.disabled = false; btn.textContent = 'Get my 15% off';
        msg.textContent = 'Something went wrong. Please try again in a moment.';
      });
    });
    document.body.appendChild(back);
    document.documentElement.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey, true);
    requestAnimationFrame(function () { back && back.classList.add('is-in'); });
    setTimeout(function () { try { email.focus({ preventScroll: true }); } catch (e) { email.focus(); } }, 50);
    track('view_promotion');
  }
  function start() { setTimeout(open, DELAY); }
  if (document.readyState !== 'loading') start(); else document.addEventListener('DOMContentLoaded', start);
})();
