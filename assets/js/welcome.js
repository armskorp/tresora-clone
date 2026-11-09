/* TRESORA welcome popup: "Create an account and get 15% off" -> opens the account page in sign-up mode.
   - Shows ~1s after the first page load; not again for 30 days after it is closed or used (localStorage).
   - Never for signed-in customers, never on account / checkout / thank-you pages. Test anytime with ?welcome=1.
   - The 15% code itself is shown on account.html to signed-in customers (redesign/shared/auth.js).
   - Turn on/off with TRESORA_CONFIG.WELCOME_POPUP (assets/js/config.js).
   Spanish text comes from i18n/es.json via the site's language switcher. */
(function () {
  var CFG = window.TRESORA_CONFIG || {};
  var FORCE = /[?&]welcome=1\b/.test(location.search);
  if (CFG.WELCOME_POPUP === false && !FORCE) return;
  var KEY = 'tresora-welcome', DAYS = 30, DELAY = 1000;
  var SIGNUP = (document.documentElement.getAttribute('data-rd-root') || '/') + 'account.html?mode=signup';
  var path = location.pathname.toLowerCase();
  if (/(^|\/)(success|cancel|cart|checkout|thank-you|thanks|account|reset-password)(\.html)?$/.test(path) || /[?&]session_id=/.test(location.search)) return;
  function signedIn() { try { for (var i = 0; i < localStorage.length; i++) { var k = localStorage.key(i); if (/^sb-.*-auth-token$/.test(k) && localStorage.getItem(k)) return true; } } catch (e) {} return false; }
  function seenRecently() { try { var t = +localStorage.getItem(KEY); return t && Date.now() - t < DAYS * 864e5; } catch (e) { return false; } }
  function remember() { try { localStorage.setItem(KEY, String(Date.now())); } catch (e) {} }
  if (signedIn() || (!FORCE && seenRecently())) return;

  /* Site palette (theme.css "taupe"): bg #dcd4c8, ink #26221e, eyebrow #4a433b; Cormorant + GT Standard; square corners. */
  var CSS = '.tw-back{position:fixed;inset:0;z-index:2147483600;background:rgba(38,34,30,.55);display:flex;align-items:center;justify-content:center;padding:16px;opacity:0;transition:opacity .25s ease}' +
    '.tw-back.is-in{opacity:1}' +
    '.tw-box{position:relative;width:100%;max-width:420px;max-height:calc(100vh - 32px);overflow:auto;box-sizing:border-box;background:#dcd4c8;color:#26221e;border:1px solid rgba(38,34,30,.24);box-shadow:0 24px 60px rgba(0,0,0,.14);padding:48px 32px 24px;text-align:center;font-family:"GT Standard",system-ui,sans-serif;transform:translateY(12px);transition:transform .25s ease}' +
    '.tw-back.is-in .tw-box{transform:none}' +
    '.tw-x{position:absolute;top:8px;right:8px;width:40px;height:40px;border:0;background:none;color:#26221e;font-size:26px;line-height:1;cursor:pointer}' +
    '.tw-x:hover{background:rgba(38,34,30,.06)}' +
    '.tw-h{margin:0 0 26px;font-family:"Cormorant",Georgia,serif;font-weight:500;font-size:34px;line-height:1.12;color:#26221e}' +
    '.tw-btn{display:flex;align-items:center;justify-content:center;height:50px;border:1px solid #26221e;background:#26221e;color:#dcd4c8;font:inherit;font-size:12px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;text-decoration:none;cursor:pointer}' +
    '.tw-btn:hover{background:#3a342e;color:#dcd4c8}' +
    '.tw-no{margin-top:14px;border:0;background:none;color:#4a433b;font:inherit;font-size:12px;letter-spacing:.06em;text-decoration:underline;cursor:pointer;padding:6px}' +
    '.tw-box :focus-visible{outline:2px solid #26221e;outline-offset:2px}' +
    '@media(max-width:480px){.tw-back{align-items:flex-end;padding:0}.tw-box{max-width:none;padding:44px 22px 20px}.tw-h{font-size:29px}}' +
    '@media(prefers-reduced-motion:reduce){.tw-back,.tw-box{transition:none}}';

  function h(tag, attrs) { var e = document.createElement(tag); for (var k in attrs) { if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]); } return e; }
  var lastFocus, back, box;
  function close() {
    if (!back) return; remember();
    document.removeEventListener('keydown', onKey, true);
    back.classList.remove('is-in'); var b = back; back = null;
    setTimeout(function () { b.remove(); document.documentElement.style.overflow = ''; }, 250);
    if (lastFocus && lastFocus.focus) try { lastFocus.focus(); } catch (e) {}
  }
  function onKey(e) {
    if (!back) return;
    if (e.key === 'Escape') { e.preventDefault(); close(); return; }
    if (e.key === 'Tab') {
      var f = [].slice.call(box.querySelectorAll('button,a[href]')); if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  }
  function track(name) { try { if (window.gtag) window.gtag('event', name, { method: 'welcome_popup' }); } catch (e) {} }

  function open() {
    if (back || signedIn() || (!FORCE && seenRecently())) return;
    if (!document.getElementById('tw-css')) document.head.appendChild(h('style', { id: 'tw-css', text: CSS }));
    lastFocus = document.activeElement;
    var x = h('button', { type: 'button', 'class': 'tw-x', 'aria-label': 'Close', text: '\u00d7' }); x.addEventListener('click', close);
    var go = h('a', { 'class': 'tw-btn', href: SIGNUP, text: 'Create account' });
    go.addEventListener('click', function () { remember(); track('select_promotion'); });
    var no = h('button', { type: 'button', 'class': 'tw-no', text: 'No thanks' }); no.addEventListener('click', close);
    box = h('div', { 'class': 'tw-box', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'tw-title' });
    box.appendChild(x);
    box.appendChild(h('h2', { 'class': 'tw-h', id: 'tw-title', text: 'Create an account and get 15% off' }));
    box.appendChild(go); box.appendChild(no);
    back = h('div', { 'class': 'tw-back', 'data-tresora-welcome': '' }); back.appendChild(box);
    back.addEventListener('mousedown', function (e) { if (e.target === back) close(); });
    document.body.appendChild(back);
    document.documentElement.style.overflow = 'hidden';
    document.addEventListener('keydown', onKey, true);
    requestAnimationFrame(function () { back && back.classList.add('is-in'); });
    setTimeout(function () { try { go.focus({ preventScroll: true }); } catch (e) { go.focus(); } }, 50);
    track('view_promotion');
  }
  function start() { setTimeout(open, DELAY); }
  if (document.readyState !== 'loading') start(); else document.addEventListener('DOMContentLoaded', start);
})();
