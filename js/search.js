/* ==========================================================================
   Search — GISTI Redesign
   Autocomplete, type filtering, keyboard navigation
   ========================================================================== */

(function () {
  'use strict';

  /* --- Autocomplete --- */
  function initAutocomplete() {
    var inputs = document.querySelectorAll('[data-autocomplete]');

    inputs.forEach(function (input) {
      var dropdown = input.parentElement.querySelector('.search-autocomplete');
      if (!dropdown) return;

      var items = dropdown.querySelectorAll('.search-autocomplete__item');
      var activeIndex = -1;

      function showDropdown() {
        var query = input.value.trim().toLowerCase();
        if (query.length < 2) {
          dropdown.classList.remove('is-open');
          return;
        }

        var hasResults = false;
        items.forEach(function (item) {
          var text = item.textContent.toLowerCase();
          var match = text.indexOf(query) !== -1;
          item.style.display = match ? '' : 'none';
          item.setAttribute('aria-selected', 'false');
          if (match) hasResults = true;
        });

        dropdown.classList.toggle('is-open', hasResults);
        activeIndex = -1;
      }

      function hideDropdown() {
        setTimeout(function () {
          dropdown.classList.remove('is-open');
        }, 200);
      }

      input.addEventListener('input', showDropdown);
      input.addEventListener('focus', showDropdown);
      input.addEventListener('blur', hideDropdown);

      input.addEventListener('keydown', function (e) {
        if (!dropdown.classList.contains('is-open')) return;

        var visibleItems = Array.from(items).filter(function (item) {
          return item.style.display !== 'none';
        });

        if (e.key === 'ArrowDown') {
          e.preventDefault();
          activeIndex = Math.min(activeIndex + 1, visibleItems.length - 1);
          updateActive(visibleItems);
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          activeIndex = Math.max(activeIndex - 1, 0);
          updateActive(visibleItems);
        } else if (e.key === 'Enter' && activeIndex >= 0) {
          e.preventDefault();
          var selected = visibleItems[activeIndex];
          if (selected && selected.href) {
            window.location.href = selected.href;
          }
        } else if (e.key === 'Escape') {
          dropdown.classList.remove('is-open');
          input.focus();
        }
      });

      function updateActive(visibleItems) {
        visibleItems.forEach(function (item, i) {
          item.setAttribute('aria-selected', i === activeIndex ? 'true' : 'false');
        });
        if (activeIndex >= 0 && visibleItems[activeIndex]) {
          visibleItems[activeIndex].scrollIntoView({ block: 'nearest' });
        }
      }
    });
  }

  /* --- Type counter filtering --- */
  function initTypeCounters() {
    var counters = document.querySelectorAll('.type-counter');
    if (!counters.length) return;

    var results = document.querySelectorAll('.search-result');

    counters.forEach(function (counter) {
      counter.addEventListener('click', function () {
        var type = counter.getAttribute('data-type');

        // Update active state
        counters.forEach(function (c) {
          c.classList.remove('is-active');
        });
        counter.classList.add('is-active');

        // Filter results
        if (!type || type === 'all') {
          results.forEach(function (r) {
            r.style.display = '';
          });
        } else {
          results.forEach(function (r) {
            var resultType = r.getAttribute('data-type');
            r.style.display = resultType === type ? '' : 'none';
          });
        }
      });
    });
  }

  /* --- Init --- */
  document.addEventListener('DOMContentLoaded', function () {
    initAutocomplete();
    initTypeCounters();
  });
})();
