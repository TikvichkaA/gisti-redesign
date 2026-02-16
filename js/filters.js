/* ==========================================================================
   Filters — GISTI Redesign
   Client-side filtering for publications, formations
   ========================================================================== */

(function () {
  'use strict';

  function initFilters() {
    var containers = document.querySelectorAll('[data-filter-container]');

    containers.forEach(function (container) {
      var items = container.querySelectorAll('[data-filter-item]');
      var selects = document.querySelectorAll('[data-filter-select]');
      var resetBtn = document.querySelector('[data-filter-reset]');
      var countEl = document.querySelector('[data-filter-count]');

      if (!items.length) return;

      function applyFilters() {
        var filters = {};

        selects.forEach(function (select) {
          var key = select.getAttribute('data-filter-select');
          var value = select.value;
          if (value) {
            filters[key] = value;
          }
        });

        var visibleCount = 0;

        items.forEach(function (item) {
          var show = true;

          Object.keys(filters).forEach(function (key) {
            var itemValue = item.getAttribute('data-' + key);
            if (itemValue !== filters[key]) {
              show = false;
            }
          });

          item.style.display = show ? '' : 'none';
          if (show) visibleCount++;
        });

        if (countEl) {
          countEl.textContent = visibleCount + ' résultat' + (visibleCount !== 1 ? 's' : '');
        }
      }

      selects.forEach(function (select) {
        select.addEventListener('change', applyFilters);
      });

      if (resetBtn) {
        resetBtn.addEventListener('click', function () {
          selects.forEach(function (select) {
            select.value = '';
          });
          applyFilters();
        });
      }

      // Initial count
      applyFilters();
    });
  }

  document.addEventListener('DOMContentLoaded', initFilters);
})();
