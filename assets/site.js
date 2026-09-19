/* Copy buttons on code blocks. That is the whole of this site's JavaScript —
   with one theme and no interactive widgets, there is nothing else to run. */
(function () {
  document.addEventListener('DOMContentLoaded', function () {
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
