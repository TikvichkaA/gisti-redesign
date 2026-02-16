/* ==========================================================================
   Tabs — GISTI Redesign
   Accessible tab interface (ARIA tablist pattern)
   ========================================================================== */

(function () {
  'use strict';

  function initTabs() {
    var tabLists = document.querySelectorAll('[role="tablist"]');

    tabLists.forEach(function (tabList) {
      var tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
      var panels = [];

      tabs.forEach(function (tab) {
        var panelId = tab.getAttribute('aria-controls');
        var panel = document.getElementById(panelId);
        if (panel) panels.push(panel);
      });

      function activateTab(tab) {
        // Deactivate all
        tabs.forEach(function (t) {
          t.setAttribute('aria-selected', 'false');
          t.setAttribute('tabindex', '-1');
        });
        panels.forEach(function (p) {
          p.setAttribute('aria-hidden', 'true');
        });

        // Activate selected
        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');

        var panelId = tab.getAttribute('aria-controls');
        var panel = document.getElementById(panelId);
        if (panel) {
          panel.setAttribute('aria-hidden', 'false');
        }
      }

      // Click handler
      tabs.forEach(function (tab) {
        tab.addEventListener('click', function (e) {
          e.preventDefault();
          activateTab(tab);
        });
      });

      // Keyboard navigation
      tabList.addEventListener('keydown', function (e) {
        var currentIndex = tabs.indexOf(document.activeElement);
        if (currentIndex === -1) return;

        var newIndex;

        if (e.key === 'ArrowRight') {
          e.preventDefault();
          newIndex = (currentIndex + 1) % tabs.length;
          tabs[newIndex].focus();
          activateTab(tabs[newIndex]);
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          newIndex = (currentIndex - 1 + tabs.length) % tabs.length;
          tabs[newIndex].focus();
          activateTab(tabs[newIndex]);
        } else if (e.key === 'Home') {
          e.preventDefault();
          tabs[0].focus();
          activateTab(tabs[0]);
        } else if (e.key === 'End') {
          e.preventDefault();
          tabs[tabs.length - 1].focus();
          activateTab(tabs[tabs.length - 1]);
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', initTabs);
})();
