/* ==========================================================================
   Table of Contents (TOC) — GISTI Redesign
   Auto-generates TOC from article headings + highlights active section
   ========================================================================== */

(function () {
  'use strict';

  function initTOC() {
    var container = document.querySelector('.toc');
    if (!container) return;

    var article = document.querySelector('.article-body .prose');
    if (!article) return;

    var headings = article.querySelectorAll('h2, h3');
    if (!headings.length) return;

    var list = container.querySelector('.toc__list');
    if (!list) return;

    // Build TOC links from headings
    var tocItems = [];

    headings.forEach(function (heading, i) {
      // Ensure heading has an id
      if (!heading.id) {
        heading.id = 'section-' + (i + 1);
      }

      var link = document.createElement('a');
      link.href = '#' + heading.id;
      link.className = 'toc__link';
      link.textContent = heading.textContent;

      if (heading.tagName === 'H3') {
        link.classList.add('toc__link--h3');
      }

      list.appendChild(link);
      tocItems.push({ link: link, heading: heading });
    });

    // Highlight active section with IntersectionObserver
    if (!('IntersectionObserver' in window) || !tocItems.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var activeId = entry.target.id;

            tocItems.forEach(function (item) {
              if (item.heading.id === activeId) {
                item.link.classList.add('is-active');
              } else {
                item.link.classList.remove('is-active');
              }
            });
          }
        });
      },
      {
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0
      }
    );

    tocItems.forEach(function (item) {
      observer.observe(item.heading);
    });
  }

  document.addEventListener('DOMContentLoaded', initTOC);
})();
