// Business Fox premium layer: sticky header shadow, current-page nav, hero stars, trust strip, scroll reveal.
(function () {
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var header = document.querySelector("body > header");
  if (header) { var onScroll = function () { header.classList.toggle("scrolled", scrollY > 8); }; addEventListener("scroll", onScroll, { passive: true }); onScroll(); }
  var here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("nav a").forEach(function (a) { if (a.getAttribute("href") === here) a.setAttribute("aria-current", "page"); });
  var hero = document.querySelector(".hero");
  if (hero && !hero.querySelector(".bf-stars")) {
    var s = document.createElement("div"); s.className = "bf-stars"; s.setAttribute("aria-hidden", "true");
    for (var i = 0; i < 22; i++) { var d = document.createElement("i"); d.style.left = (Math.random() * 96 + 2) + "%"; d.style.top = (Math.random() * 70 + 4) + "%"; d.style.animationDelay = (Math.random() * 4).toFixed(2) + "s"; d.style.animationDuration = (3 + Math.random() * 3).toFixed(2) + "s"; s.appendChild(d); }
    hero.prepend(s);
    if (!document.querySelector(".bf-trust")) {
      var t = document.createElement("div"); t.className = "bf-trust";
      t.innerHTML = '<span><b>✓</b>Secure Square checkout</span><span><b>✓</b>Card, Apple Pay, Google Pay or Cash App Pay</span><span><b>✓</b>Printables emailed right after payment</span><span><b>✓</b>Every order checked before it goes out</span>';
      hero.after(t);
    }
  }
  if (reduce || !("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("bf-in"); io.unobserve(e.target); } }); }, { rootMargin: "0px 0px -40px 0px" });
  document.querySelectorAll(".grid .card, main > h2, .bf-trust, ul.inc").forEach(function (el, i) {
    if (el.getBoundingClientRect().top < innerHeight) return; // already on screen: show immediately
    el.classList.add("bf-reveal"); el.style.transitionDelay = ((i % 4) * 60) + "ms"; io.observe(el);
  });
})();
