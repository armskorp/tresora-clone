/* Homepage Santa: fly once when the hero is in view, and again each time the visitor scrolls back to the top. Stays on the first slide only. */
(function(){
  var hero = document.querySelector("[data-rd-slides]");
  var wrap = hero && hero.querySelector("[data-rd-santa]");
  if (!hero || !wrap) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var vid = wrap.querySelector("video");
  var img = wrap.querySelector("img");
  var bob = wrap.querySelector(".rd-santa__bob");
  var useVideo = !!(vid && vid.canPlayType && vid.canPlayType('video/webm; codecs="vp9"'));
  var webpSrc = "/redesign/shared/products/santa-sleigh-fly.webp?v=20261110d";
  if (!useVideo) {
    wrap.classList.add("rd-santa--img");
    if (!img) {
      img = document.createElement("img");
      img.className = "rd-santa__img";
      img.alt = "";
      img.width = 1474;
      img.height = 454;
      img.decoding = "async";
      img.src = webpSrc;
      wrap.querySelector(".rd-santa__bob").appendChild(img);
    }
  }

  var away = true;
  var unlockTimer = null;
  hero.dispatchEvent(new Event("rd-santa-hold"));

  function lockFirst(){
    hero.dispatchEvent(new Event("rd-santa-lock"));
  }
  function unlock(){
    if (unlockTimer) { clearTimeout(unlockTimer); unlockTimer = null; }
    hero.dispatchEvent(new Event("rd-santa-unlock"));
  }

  function play(){
    lockFirst();
    wrap.classList.remove("is-play");
    void wrap.offsetWidth;
    wrap.classList.add("is-play");
    if (useVideo && vid) {
      try {
        vid.pause();
        vid.currentTime = 0;
        var p = vid.play();
        if (p && p.catch) p.catch(function(){});
      } catch (e) {}
    } else if (img) {
      img.src = webpSrc + "&r=" + Date.now();
    }
    if (unlockTimer) clearTimeout(unlockTimer);
    unlockTimer = setTimeout(unlock, 8300);
  }

  if (bob) {
    bob.addEventListener("animationend", function(e){
      if (e.animationName === "rd-santa-fly") unlock();
    });
  }

  function startWhenReady(fn){
    if (useVideo && vid) {
      if (vid.readyState >= 3) { fn(); return; }
      vid.addEventListener("canplaythrough", fn, { once: true });
      vid.addEventListener("error", fn, { once: true });
      try { vid.load(); } catch (e) {}
      return;
    }
    if (!img || img.complete) { fn(); return; }
    img.addEventListener("load", fn, { once: true });
    img.addEventListener("error", fn, { once: true });
  }

  startWhenReady(function(){
    if (!("IntersectionObserver" in window)) { play(); return; }
    var io = new IntersectionObserver(function(entries){
      var e = entries[0];
      if (e.isIntersecting && e.intersectionRatio >= 0.4) {
        if (away) { away = false; play(); }
      } else if (e.intersectionRatio < 0.12) {
        away = true;
        wrap.classList.remove("is-play");
        if (vid) try { vid.pause(); } catch (err) {}
        unlock();
      }
    }, { threshold: [0, 0.12, 0.4, 0.7, 1] });
    io.observe(hero);
  });
})();
