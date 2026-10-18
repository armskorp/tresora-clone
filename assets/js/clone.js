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
    // go to the previous/next laid-out slide exactly (card galleries have no scroll-snap in the copy)
    var step = function (dir) {
      var slides = Array.prototype.filter.call(track.children, function (el) {
        return el.tagName === 'SLIDESHOW-SLIDE' && el.offsetWidth > 0;
      });
      if (!slides.length) return;
      var cur = 0, best = Infinity;
      slides.forEach(function (el, i) { var d = Math.abs(el.offsetLeft - track.scrollLeft); if (d < best) { best = d; cur = i; } });
      var next = Math.max(0, Math.min(slides.length - 1, cur + dir));
      track.scrollTo({ left: slides[next].offsetLeft, behavior: 'smooth' });
    };
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

  /* 6. Horizon sets `in-viewport` on carousels from JS; without it the theme CSS forces overflow:hidden,
        so on phones the product / collection rows could not be swiped and their right half was unreachable. */
  document.querySelectorAll('slideshow-component').forEach(function (show) { show.setAttribute('in-viewport', ''); });

  /* 7. Images: the snapshot keeps loading="lazy" on gallery slides, menu thumbnails and hidden variant slides.
        Lazy images inside clipped/overflow-hidden tracks or hidden menus never intersect the viewport, so the
        browser never fetches them and a card can end up showing an empty frame. Load a card's images as soon as
        it comes near the screen, and everything else once the page is idle. */
  var eager = function (img) {
    // only ever upgrade lazy -> eager; never touch src/decoding of an image that is already shown
    if (img.getAttribute('loading') === 'lazy') img.setAttribute('loading', 'eager');
  };
  var groups = document.querySelectorAll('product-card, .resource-card, slideshow-component');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.querySelectorAll('img').forEach(eager);
        io.unobserve(en.target);
      });
    }, { rootMargin: '800px 800px' });
    groups.forEach(function (g) { io.observe(g); });
  } else {
    document.querySelectorAll('img').forEach(eager);
  }
  var loadRest = function () { document.querySelectorAll('img[loading="lazy"]').forEach(eager); };
  window.addEventListener('load', function () {
    (window.requestIdleCallback || function (f) { setTimeout(f, 1200); })(loadRest, { timeout: 3000 });
  });
  document.querySelectorAll('product-card, .header-menu, header-menu').forEach(function (el) {
    el.addEventListener('pointerenter', function () { el.querySelectorAll('img').forEach(eager); }, { once: true });
  });

  /* 8. Sticky header state (normally done by Horizon's header.js). Without it the transparent header stayed
        transparent while sticky and its logo/icons were drawn on top of the page content on phones. */
  var header = document.getElementById('header-component');
  if (header) {
    var section = header.closest('.header-section') || header.parentElement;
    var lastY = window.scrollY, ticking = false;
    var sync = function () {
      ticking = false;
      var y = Math.max(0, window.scrollY);
      // the header's resting position = everything above it in the header group (announcement bar);
      // offsetTop of a stuck sticky element moves with it, so it can't be used here
      var start = 0, n = section && section.previousElementSibling;
      while (n) { start += n.offsetHeight; n = n.previousElementSibling; }
      header.setAttribute('data-sticky-state', y > start + 1 ? 'active' : 'inactive');
      header.setAttribute('data-scroll-direction', y <= 0 ? 'none' : (y > lastY ? 'down' : (y < lastY ? 'up' : header.getAttribute('data-scroll-direction') || 'none')));
      lastY = y;
    };
    var layout = function () {
      header.setAttribute('data-menu-style', window.matchMedia('(max-width: 749px)').matches ? 'drawer' : 'menu');
      var row = header.offsetHeight;
      if (row) document.body.style.setProperty('--header-height', row + 'px');
      var group = document.getElementById('header-group');
      var bar = group && group.querySelector('.shopify-section:not(.header-section)');
      if (bar) document.body.style.setProperty('--header-group-height', bar.offsetHeight + 'px');
      sync();
    };
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(sync); } }, { passive: true });
    window.addEventListener('resize', layout);
    window.addEventListener('orientationchange', layout);
    layout();
  }

  /* 5. Non-functional controls in a static copy: keep them from navigating */
  document.querySelectorAll('a[href="#"]').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); });
  });
})();
