/* Theme toggle + copy buttons. Kept small and dependency-free — a static site
   for a single-binary tool should not ship a framework.

   The toggle's icon is two inline SVGs in the markup; CSS decides which one is
   visible. That way the button is already correct before this script runs, and
   stays correct if the script never loads at all. */
(function () {
  var root = document.documentElement;

  function stored() {
    try { return localStorage.getItem('reachmap-theme'); } catch (e) { return null; }
  }

  function apply(t) {
    if (t === 'light' || t === 'dark') root.setAttribute('data-theme', t);
    else root.removeAttribute('data-theme');
  }

  function current() {
    var explicit = root.getAttribute('data-theme');
    if (explicit) return explicit;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  apply(stored());

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.querySelector('.theme-toggle');
    if (btn) {
      var label = function () {
        var next = current() === 'light' ? 'dark' : 'light';
        btn.setAttribute('aria-label', 'Switch to ' + next + ' theme');
      };
      label();
      btn.addEventListener('click', function () {
        var next = current() === 'light' ? 'dark' : 'light';
        apply(next);
        try { localStorage.setItem('reachmap-theme', next); } catch (e) {}
        label();
      });
      // A system theme change should move the label too, unless the visitor has
      // made an explicit choice.
      var mq = window.matchMedia('(prefers-color-scheme: light)');
      if (mq.addEventListener) mq.addEventListener('change', label);
    }

    document.querySelectorAll('.term .copy').forEach(function (b) {
      b.addEventListener('click', function () {
        var pre = b.closest('.term').querySelector('pre');
        if (!pre) return;
        var done = function () {
          b.textContent = 'copied';
          setTimeout(function () { b.textContent = 'copy'; }, 1400);
        };
        if (navigator.clipboard) navigator.clipboard.writeText(pre.innerText).then(done, function () {});
        else done();
      });
    });
  });
})();
