/* ==========================================================================
   Main JS — GISTI Redesign
   Navigation, scroll, reveal, alert banner, header search
   ========================================================================== */

(function () {
  'use strict';

  /* --- Mobile Navigation Toggle --- */
  function initMobileNav() {
    const toggle = document.querySelector('.mobile-nav-toggle');
    const nav = document.querySelector('.mobile-nav');
    if (!toggle || !nav) return;

    toggle.addEventListener('click', function () {
      const isOpen = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!isOpen));
      nav.classList.toggle('is-open', !isOpen);
      document.body.style.overflow = !isOpen ? 'hidden' : '';
    });

    // Sub-menu toggles in mobile
    nav.querySelectorAll('[data-mobile-submenu]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const subId = btn.getAttribute('data-mobile-submenu');
        const sub = document.getElementById(subId);
        if (!sub) return;
        const isOpen = sub.classList.contains('is-open');
        sub.classList.toggle('is-open', !isOpen);
        btn.setAttribute('aria-expanded', String(!isOpen));
      });
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('is-open')) {
        toggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('is-open');
        document.body.style.overflow = '';
        toggle.focus();
      }
    });
  }

  /* --- Desktop Mega-Menu --- */
  function initMegaMenu() {
    var menuItems = document.querySelectorAll('[data-mega-menu]');

    menuItems.forEach(function (item) {
      var trigger = item.querySelector('.main-nav__link');
      var menu = item.querySelector('.mega-menu');
      if (!trigger || !menu) return;
      var closeTimeout;

      function open() {
        clearTimeout(closeTimeout);
        // Close other menus
        menuItems.forEach(function (other) {
          if (other !== item) {
            var otherMenu = other.querySelector('.mega-menu');
            var otherTrigger = other.querySelector('.main-nav__link');
            if (otherMenu) otherMenu.classList.remove('is-open');
            if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
          }
        });
        menu.classList.add('is-open');
        trigger.setAttribute('aria-expanded', 'true');
      }

      function close() {
        closeTimeout = setTimeout(function () {
          menu.classList.remove('is-open');
          trigger.setAttribute('aria-expanded', 'false');
        }, 150);
      }

      item.addEventListener('mouseenter', open);
      item.addEventListener('mouseleave', close);

      trigger.addEventListener('click', function (e) {
        if (menu.classList.contains('is-open')) {
          close();
        } else {
          e.preventDefault();
          open();
        }
      });

      trigger.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (menu.classList.contains('is-open')) {
            menu.classList.remove('is-open');
            trigger.setAttribute('aria-expanded', 'false');
          } else {
            open();
            var firstLink = menu.querySelector('a');
            if (firstLink) firstLink.focus();
          }
        }
      });

      // Close on escape
      menu.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          menu.classList.remove('is-open');
          trigger.setAttribute('aria-expanded', 'false');
          trigger.focus();
        }
      });
    });
  }

  /* --- Header Scroll Shadow --- */
  function initScrollShadow() {
    var header = document.querySelector('.site-header');
    if (!header) return;

    var scrolled = false;

    function onScroll() {
      var shouldBeScrolled = window.scrollY > 10;
      if (shouldBeScrolled !== scrolled) {
        scrolled = shouldBeScrolled;
        requestAnimationFrame(function () {
          header.classList.toggle('is-scrolled', scrolled);
        });
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* --- Scroll Reveal (IntersectionObserver) --- */
  function initScrollReveal() {
    var elements = document.querySelectorAll('.reveal');
    if (!elements.length) return;

    if (!('IntersectionObserver' in window)) {
      elements.forEach(function (el) {
        el.classList.add('is-visible');
      });
      return;
    }

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    elements.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* --- Alert Banner Dismiss --- */
  function initAlertBanner() {
    var banner = document.querySelector('.alert-banner');
    if (!banner) return;

    var closeBtn = banner.querySelector('.alert-banner__close');
    if (!closeBtn) return;

    closeBtn.addEventListener('click', function () {
      banner.style.height = banner.offsetHeight + 'px';
      requestAnimationFrame(function () {
        banner.style.transition = 'height 300ms ease, opacity 300ms ease';
        banner.style.height = '0';
        banner.style.opacity = '0';
        banner.style.overflow = 'hidden';
      });
      setTimeout(function () {
        banner.remove();
      }, 300);
    });
  }

  /* --- Header Search --- */
  function initHeaderSearch() {
    var searchBtn = document.querySelector('.header-search-btn');
    var searchPanel = document.querySelector('.header-search');
    if (!searchBtn || !searchPanel) return;

    var input = searchPanel.querySelector('.header-search__input');
    var closeBtn = searchPanel.querySelector('.header-search__close');

    function openSearch() {
      searchPanel.classList.add('is-open');
      if (input) input.focus();
    }

    function closeSearch() {
      searchPanel.classList.remove('is-open');
      searchBtn.focus();
    }

    searchBtn.addEventListener('click', openSearch);

    if (closeBtn) {
      closeBtn.addEventListener('click', closeSearch);
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && searchPanel.classList.contains('is-open')) {
        closeSearch();
      }
    });
  }

  /* --- Smooth scroll for anchor links --- */
  function initSmoothScroll() {
    document.addEventListener('click', function (e) {
      var link = e.target.closest('a[href^="#"]');
      if (!link) return;

      var targetId = link.getAttribute('href');
      if (targetId === '#') return;

      var target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();
      var offset = 80; // header height
      var top = target.getBoundingClientRect().top + window.scrollY - offset;

      window.scrollTo({ top: top, behavior: 'smooth' });

      // Update focus for a11y
      target.setAttribute('tabindex', '-1');
      target.focus({ preventScroll: true });
    });
  }

  /* --- Init all on DOMContentLoaded --- */
  document.addEventListener('DOMContentLoaded', function () {
    initMobileNav();
    initMegaMenu();
    initScrollShadow();
    initScrollReveal();
    initAlertBanner();
    initHeaderSearch();
    initSmoothScroll();
  });
})();
