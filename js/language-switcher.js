/* ==========================================================================
   Language Switcher — GISTI Redesign
   Switches displayed content for multilingual asylum guide
   ========================================================================== */

(function () {
  'use strict';

  function initLanguageSwitcher() {
    var containers = document.querySelectorAll('[data-lang-switcher]');

    containers.forEach(function (container) {
      var buttons = container.querySelectorAll('.lang-switcher__btn');
      var groupId = container.getAttribute('data-lang-switcher');
      var contents = document.querySelectorAll('[data-lang-group="' + groupId + '"]');

      if (!buttons.length || !contents.length) return;

      buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
          var lang = btn.getAttribute('data-lang');

          // Update button states
          buttons.forEach(function (b) {
            b.classList.remove('is-active');
            b.setAttribute('aria-pressed', 'false');
          });
          btn.classList.add('is-active');
          btn.setAttribute('aria-pressed', 'true');

          // Show matching content
          contents.forEach(function (content) {
            if (content.getAttribute('data-lang') === lang) {
              content.classList.add('is-active');
            } else {
              content.classList.remove('is-active');
            }
          });
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initLanguageSwitcher);
})();
