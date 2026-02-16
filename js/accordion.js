/* ==========================================================================
   Accordion — GISTI Redesign
   Accessible collapsible sections (ARIA compliant)
   ========================================================================== */

(function () {
  'use strict';

  function initAccordions() {
    var accordions = document.querySelectorAll('.accordion');

    accordions.forEach(function (accordion) {
      var triggers = accordion.querySelectorAll('.accordion__trigger');

      triggers.forEach(function (trigger) {
        trigger.addEventListener('click', function () {
          var panelId = trigger.getAttribute('aria-controls');
          var panel = document.getElementById(panelId);
          if (!panel) return;

          var isOpen = trigger.getAttribute('aria-expanded') === 'true';

          // Close all panels in this accordion (single-open mode)
          if (!accordion.hasAttribute('data-multi')) {
            triggers.forEach(function (t) {
              var pId = t.getAttribute('aria-controls');
              var p = document.getElementById(pId);
              t.setAttribute('aria-expanded', 'false');
              if (p) p.setAttribute('aria-hidden', 'true');
            });
          }

          // Toggle current
          if (isOpen) {
            trigger.setAttribute('aria-expanded', 'false');
            panel.setAttribute('aria-hidden', 'true');
          } else {
            trigger.setAttribute('aria-expanded', 'true');
            panel.setAttribute('aria-hidden', 'false');
          }
        });

        // Keyboard support
        trigger.addEventListener('keydown', function (e) {
          var triggers = Array.from(accordion.querySelectorAll('.accordion__trigger'));
          var index = triggers.indexOf(trigger);

          if (e.key === 'ArrowDown') {
            e.preventDefault();
            var next = triggers[(index + 1) % triggers.length];
            next.focus();
          } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            var prev = triggers[(index - 1 + triggers.length) % triggers.length];
            prev.focus();
          } else if (e.key === 'Home') {
            e.preventDefault();
            triggers[0].focus();
          } else if (e.key === 'End') {
            e.preventDefault();
            triggers[triggers.length - 1].focus();
          }
        });
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initAccordions);
})();
