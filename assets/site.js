/* Copy buttons, and a one-shot reveal for diagrams.

   The reveal is additive by design: the stylesheet already renders every
   diagram in its finished state, and the animations only play *into* that
   state. So if this file fails to load, or IntersectionObserver is missing, or
   the reader has asked for reduced motion, the page is still correct — it just
   does not move. That is the opposite of the usual reveal-on-scroll setup,
   where the base stylesheet hides everything and a scripting failure leaves a
   blank page. */
(function () {
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var figures = document.querySelectorAll('.dia');

    if (!('IntersectionObserver' in window)) {
      // No observer: play everything now rather than never.
      figures.forEach(function (f) { f.classList.add('in-view'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);   // once, not on every scroll past
        });
      }, { threshold: 0.2, rootMargin: '0px 0px -8% 0px' });
      figures.forEach(function (f) { io.observe(f); });
    }

    document.querySelectorAll('.term .copy').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var pre = btn.closest('.term').querySelector('pre');
        if (!pre) return;
        var done = function () {
          btn.textContent = 'copied';
          setTimeout(function () { btn.textContent = 'copy'; }, 1400);
        };
        if (navigator.clipboard) navigator.clipboard.writeText(pre.innerText).then(done, function () {});
        else done();
      });
    });
  });
})();
