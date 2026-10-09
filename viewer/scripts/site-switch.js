// The AdaptBase site switcher (<details class="site-switch">): close it on a
// click outside or on Escape. Opening and keyboard use are the browser's own
// <details>/<summary> behaviour. The same script is on search.adaptbase.us,
// plans.adaptbase.us and ontology.adaptbase.us.
(function () {
  document.querySelectorAll('details.site-switch').forEach(function (d) {
    document.addEventListener('click', function (e) {
      if (d.open && !d.contains(e.target)) d.open = false;
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && d.open) {
        d.open = false;
        d.querySelector('summary').focus();
      }
    });
  });
})();
