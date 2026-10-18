/* Minimal behaviour for the static TRESORA homepage copy.
   Replaces the parts of the Shopify/Horizon + Judge.me runtime that affect layout or basic interaction. */
(function () {
  'use strict';

  /* 1. Mobile menu drawer (<details> based) */
  var drawer = document.getElementById('Details-menu-drawer-container');
  if (drawer) {
    var summary = drawer.querySelector('summary');
    var setOpen = function (open) {
      drawer.open = open;
      drawer.classList.toggle('menu-open', open);
      if (summary) summary.setAttribute('aria-expanded', String(open));
      document.documentElement.style.overflow = open ? 'hidden' : '';
    };
    summary && summary.addEventListener('click', function (e) { e.preventDefault(); setOpen(!drawer.open); });
    drawer.querySelectorAll('.menu-drawer__backdrop, .menu-drawer__close-button').forEach(function (el) {
      el.addEventListener('click', function (e) { e.preventDefault(); setOpen(false); });
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && drawer.open) setOpen(false); });
  }

  /* 2. Desktop header menu: show submenu on hover / focus */
  var headerMenu = document.querySelector('header-menu');
  if (headerMenu) {
    var close = function () {
      headerMenu.querySelectorAll('[data-active]').forEach(function (s) { s.removeAttribute('data-active'); });
      headerMenu.querySelectorAll('.menu-list__link[aria-expanded]').forEach(function (a) { a.setAttribute('aria-expanded', 'false'); });
      headerMenu.removeAttribute('aria-expanded');
      headerMenu.style.removeProperty('--submenu-opacity');
    };
    headerMenu.querySelectorAll('.menu-list__list-item').forEach(function (item) {
      var sub = item.querySelector('.menu-list__submenu');
      var link = item.querySelector('.menu-list__link');
      var open = function () {
        close();
        if (!sub) return;
        sub.setAttribute('data-active', '');
        link && link.setAttribute('aria-expanded', 'true');
        headerMenu.setAttribute('aria-expanded', 'true');
        headerMenu.style.setProperty('--submenu-opacity', '1');
      };
      item.addEventListener('pointerenter', open);
      item.addEventListener('focusin', open);
    });
    headerMenu.addEventListener('pointerleave', close);
  }

  /* 3. Horizon slideshows (product card galleries): arrow buttons scroll the slide track */
  document.querySelectorAll('slideshow-component').forEach(function (show) {
    var track = show.querySelector('slideshow-slides');
    if (!track) return;
    var step = function (dir) { track.scrollBy({ left: dir * track.clientWidth, behavior: 'smooth' }); };
    show.querySelectorAll('.slideshow-control--previous').forEach(function (b) {
      b.disabled = false; b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); step(-1); });
    });
    show.querySelectorAll('.slideshow-control--next').forEach(function (b) {
      b.disabled = false; b.addEventListener('click', function (e) { e.preventDefault(); e.stopPropagation(); step(1); });
    });
  });

  /* 4. Judge.me cards carousel: position on first real review, prev/next + swipe, infinite loop via clones */
  document.querySelectorAll('.jdgm-cards-carousel').forEach(function (w) {
    var c = w.querySelector('.jdgm-videos-container');
    if (!c) return;
    var cards = Array.prototype.slice.call(c.children);
    var real = cards.filter(function (el) { return !el.dataset.cloneType; });
    if (!real.length) return;
    var first = cards.indexOf(real[0]);
    var idx = first;
    var go = function (i, animate) {
      idx = i;
      c.style.transition = animate ? 'transform .4s ease' : 'none';
      c.style.transform = 'translateX(' + (-cards[idx].offsetLeft) + 'px)';
      cards.forEach(function (el, k) { el.classList.toggle('active', k === idx); });
    };
    c.addEventListener('transitionend', function () {
      if (idx >= first + real.length) go(idx - real.length, false);
      else if (idx < first) go(idx + real.length, false);
    });
    var move = function (d) { var n = idx + d; if (n < 0 || n >= cards.length) return; go(n, true); };
    var id = w.dataset.jdgmBlockId;
    w.querySelectorAll('.jdgm-arrow').forEach(function (b, k) {
      b.removeAttribute('onclick');
      b.addEventListener('click', function () { move(/Previous/i.test(b.getAttribute('aria-label') || '') ? -1 : 1); });
    });
    window.jdgmPreviousCard = window.jdgmPreviousCard || function () {};
    window.jdgmNextCard = window.jdgmNextCard || function () {};
    var x0 = null;
    c.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    c.addEventListener('touchend', function (e) {
      if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 40) move(dx < 0 ? 1 : -1);
    });
    go(first, false);
    window.addEventListener('resize', function () { go(idx, false); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { go(idx, false); });
  });

  /* 5. Non-functional controls in a static copy: keep them from navigating */
  document.querySelectorAll('a[href="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); });
  });
})();
