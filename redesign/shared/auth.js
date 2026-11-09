/* TRESORA accounts (Supabase Auth): sign up, sign in, sign out, forgot / reset password, "My account" panel.
   Messages are plain English strings; i18n.js translates them to Spanish when ES is selected. */
(function () {
  var $ = function (s, r) { return (r || document).querySelector(s); }, $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var C = window.TRESORA_AUTH, lib = window.supabase;
  var emailOk = function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v).trim()); };
  var ap = $('[data-rd-accountpage]'), rp = $('[data-rd-resetpage]');
  var say = function (el, txt, ok) { el.className = 'rd-auth__msg ' + (ok ? 'is-ok' : 'is-error'); el.textContent = txt; };
  if (!C || !lib) { var m0 = $('[data-rd-msg]'); if (m0) say(m0, 'Accounts are temporarily unavailable. Please try again later.'); return; }
  var sb = lib.createClient(C.URL, C.KEY, { auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true } });
  window.TRESORA_SB = sb;
  var errText = function (err) {
    var c = (err && (err.code || '')) + ' ' + (err && err.message || '');
    if (/invalid_credentials|Invalid login credentials/i.test(c)) return 'Incorrect email or password.';
    if (/email_not_confirmed|not confirmed/i.test(c)) return 'Please confirm your email first. Check your inbox for the link.';
    if (/user_already_exists|already registered/i.test(c)) return 'An account with this email already exists. Please sign in.';
    if (/weak_password|Password should/i.test(c)) return 'Please choose a stronger password (at least 8 characters).';
    if (/rate|too many|over_email_send_rate_limit|429/i.test(c)) return 'Too many attempts. Please wait a few minutes and try again.';
    if (/same_password|different from the old/i.test(c)) return 'Please choose a password you have not used before.';
    if (/session|expired|Auth session missing/i.test(c)) return 'This link has expired. Please request a new one.';
    return 'Something went wrong. Please try again.';
  };
  var wireShow = function (scope) {
    $$('[data-rd-showpass]', scope).forEach(function (b) { b.addEventListener('click', function () {
      var p = b.parentNode.querySelector('input'), show = p.type === 'password'; p.type = show ? 'text' : 'password'; b.textContent = show ? 'Hide' : 'Show';
    }); });
  };
  var header = function (on) {
    $$('[data-rd-account]').forEach(function (a) { a.classList.toggle('is-in', on); a.setAttribute('aria-label', on ? 'My account' : 'Account'); var s = a.querySelector('span'); if (s) s.textContent = on ? 'My account' : 'Account'; });
    $$('.rd-nav__acc').forEach(function (a) { a.textContent = on ? 'My account' : 'Account'; });
  };

  if (ap) {
    var auth = $('[data-rd-auth]', ap), msg = $('[data-rd-msg]', auth), out = $('[data-rd-out]', ap), inn = $('[data-rd-in]', ap), submit = $('[data-rd-submit]', ap);
    var TITLES = { signin: 'Welcome back', signup: 'Create your account', forgot: 'Reset your password' };
    var BTN = { signin: 'Sign in', signup: 'Create account', forgot: 'Send reset link' };
    var mode = function (m) {
      ap.setAttribute('data-mode', m);
      $$('[data-rd-tab]', ap).forEach(function (t) { t.setAttribute('aria-selected', String(t.getAttribute('data-rd-tab') === m)); });
      $('[data-rd-modal-title]', ap).textContent = TITLES[m]; submit.textContent = BTN[m];
      auth.password.setAttribute('autocomplete', m === 'signup' ? 'new-password' : 'current-password');
      msg.textContent = ''; msg.className = 'rd-auth__msg';
    };
    var params = new URLSearchParams(location.search);
    mode(params.get('mode') === 'signup' ? 'signup' : 'signin');
    $$('[data-rd-tab]', ap).forEach(function (t) { t.addEventListener('click', function () { mode(t.getAttribute('data-rd-tab')); }); });
    $('[data-rd-forgot]', ap).addEventListener('click', function () { mode('forgot'); auth.email.focus(); });
    $('[data-rd-back]', ap).addEventListener('click', function () { mode('signin'); });
    wireShow(ap);
    var busy = function (on) { submit.disabled = on; ap.classList.toggle('is-busy', on); };
    var render = function (session) {
      var on = !!session; header(on);
      out.hidden = on; inn.hidden = !on; ap.classList.toggle('is-in', on);
      if (on) {
        $('[data-rd-email]', ap).textContent = session.user.email;
        sb.from('profiles').select('newsletter').eq('id', session.user.id).maybeSingle().then(function (r) { if (r.data) $('[data-rd-newsopt]', ap).checked = !!r.data.newsletter; });
      }
    };
    auth.addEventListener('submit', function (e) {
      e.preventDefault();
      var m = ap.getAttribute('data-mode'), email = auth.email.value.trim(), pw = auth.password.value;
      if (!emailOk(email)) { say(msg, 'Please enter a valid email address.'); auth.email.focus(); return; }
      if (m !== 'forgot' && pw.length < 8) { say(msg, 'Password must be at least 8 characters.'); auth.password.focus(); return; }
      busy(true); say(msg, 'Please wait…', true);
      var done = function () { busy(false); };
      if (m === 'signup') {
        sb.auth.signUp({ email: email, password: pw, options: { emailRedirectTo: C.SITE + 'account.html?welcome=1', data: { full_name: auth.name.value.trim(), newsletter: auth.news.checked } } })
          .then(function (r) {
            done();
            if (r.error) return say(msg, errText(r.error));
            if (r.data && r.data.user && r.data.user.identities && r.data.user.identities.length === 0) return say(msg, 'An account with this email already exists. Please sign in.');
            if (r.data.session) return render(r.data.session);
            auth.password.value = ''; ap.setAttribute('data-sent', '1');
            say(msg, 'Almost there! We sent a confirmation link to your email. Open it to activate your account and get your 15% welcome code.', true);
          }, function () { done(); say(msg, 'Something went wrong. Please try again.'); });
      } else if (m === 'signin') {
        sb.auth.signInWithPassword({ email: email, password: pw }).then(function (r) {
          done(); if (r.error) return say(msg, errText(r.error)); auth.password.value = ''; render(r.data.session);
        }, function () { done(); say(msg, 'Something went wrong. Please try again.'); });
      } else {
        sb.auth.resetPasswordForEmail(email, { redirectTo: C.SITE + 'reset-password.html' }).then(function (r) {
          done(); if (r.error) return say(msg, errText(r.error));
          say(msg, 'If an account exists for this email, a reset link is on its way.', true);
        }, function () { done(); say(msg, 'Something went wrong. Please try again.'); });
      }
    });
    $('[data-rd-logout]', ap).addEventListener('click', function () { sb.auth.signOut().then(function () { render(null); mode('signin'); say(msg, 'You have been logged out.', true); }); });
    $('[data-rd-copy]', ap).addEventListener('click', function (e) {
      var b = e.target; try { navigator.clipboard.writeText(((window.TRESORA_CONFIG || {}).WELCOME_CODE) || 'WELCOME15').then(function () { b.textContent = 'Copied'; }); } catch (x) {}
    });
    $('[data-rd-newsopt]', ap).addEventListener('change', function (e) {
      var im = $('[data-rd-inmsg]', ap);
      sb.auth.getUser().then(function (u) {
        if (!u.data.user) return;
        sb.from('profiles').update({ newsletter: e.target.checked }).eq('id', u.data.user.id).then(function (r) { say(im, r.error ? 'Something went wrong. Please try again.' : 'Preferences saved.', !r.error); });
      });
    });
    if (/error_description=/.test(location.hash)) say(msg, 'This link has expired. Please request a new one.');
    sb.auth.getSession().then(function (r) { render(r.data.session); });
    sb.auth.onAuthStateChange(function (ev, session) { if (ev === 'SIGNED_IN' || ev === 'SIGNED_OUT') render(session); });
  }

  if (rp) {
    var f = $('[data-rd-reset]', rp), rm = $('[data-rd-msg]', f); wireShow(rp);
    var ready = false;
    sb.auth.onAuthStateChange(function (ev, s) { if (s) ready = true; });
    sb.auth.getSession().then(function (r) { if (r.data.session) ready = true; else setTimeout(function () { if (!ready) say(rm, 'Open this page from the reset link in your email.'); }, 1500); });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (f.password.value.length < 8) return say(rm, 'Password must be at least 8 characters.');
      sb.auth.updateUser({ password: f.password.value }).then(function (r) {
        if (r.error) return say(rm, errText(r.error));
        f.password.value = ''; header(true); say(rm, 'Your password has been updated. You are now signed in.', true);
        setTimeout(function () { location.href = 'account.html'; }, 1800);
      });
    });
  } else if (!ap) {
    sb.auth.getSession().then(function (r) { header(!!r.data.session); });
  }
})();
