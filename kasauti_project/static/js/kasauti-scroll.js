/* =========================================================
   KASAUTI — GSAP Scroll Experience
   ScrollSmoother + ScrollTrigger — gsap.com jaisa feel
   ========================================================= */
(function () {
  'use strict';

  if (typeof gsap === 'undefined') return;

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

  document.addEventListener('DOMContentLoaded', function () {

    /* ============================================
       1) SCROLLSMOOTHER — buttery smooth scroll
       ============================================ */
    var smoother = null;
    var wrapper = document.getElementById('smooth-wrapper');

    if (wrapper && !reduced) {
      smoother = ScrollSmoother.create({
        wrapper: '#smooth-wrapper',
        content: '#smooth-content',
        smooth: 1.4,
        effects: true,
        smoothTouch: 0.1,
        normalizeScroll: false
      });
    }

    if (reduced) {
      gsap.set('.reveal', { clearProps: 'all', opacity: 1 });
      return;
    }

    /* ============================================
       2) HERO — page load entrance
       ============================================ */
    var heroItems = [
      '.hero-content .welcome-text',
      '.hero-content .animated-text',
      '.hero-content .importer',
      '.hero-content .phegraph',
      '.hero-content .items',
      '.hero-content .hero-buttons'
    ].map(function (s) { return document.querySelector(s); }).filter(Boolean);

    if (heroItems.length) {
      gsap.from(heroItems, {
        y: 45,
        opacity: 0,
        duration: 1.1,
        ease: 'power4.out',
        stagger: 0.12,
        delay: 0.15,
        clearProps: 'all'
      });
    }

    var heroCar = document.querySelector('.hero-carousel');
    if (heroCar) {
      gsap.from(heroCar, {
        opacity: 0, scale: 0.92, duration: 1.3,
        ease: 'power4.out', delay: 0.45, clearProps: 'all'
      });
    }

    /* ============================================
       3) PARALLAX — headings alag speed pe
       ============================================ */
    if (smoother) {
      var speeds = [
        ['.core-products-head', 0.92],
        ['.calc-head',          0.92],
        ['.compare-head',       0.92],
        ['.process-head',       0.92],
        ['.reviews-head',       0.92],
        ['.reels-head',         0.92],
        ['.faq-head',           0.92],
        ['.faq-side-card',      0.88],
        ['.final-cta-glow',     0.75]
      ];
      speeds.forEach(function (pair) {
        document.querySelectorAll(pair[0]).forEach(function (el) {
          el.setAttribute('data-speed', pair[1]);
        });
      });
      smoother.effects('[data-speed]');
    }

    /* ============================================
       4) STAGGER GROUPS — cards ek-ek karke
       ============================================ */
    document.querySelectorAll('.stagger-group').forEach(function (grid) {
      var kids = grid.querySelectorAll('.reveal');
      if (!kids.length) kids = grid.children;
      gsap.from(kids, {
        y: 70,
        opacity: 0,
        scale: 0.96,
        duration: 1.1,
        ease: 'power4.out',
        stagger: 0.12,
        clearProps: 'all',
        scrollTrigger: {
          trigger: grid,
          start: 'top 85%',
          once: true
        }
      });
    });

    /* ============================================
       5) SINGLE REVEALS — headings, table, CTA
       ============================================ */
    gsap.utils.toArray('.reveal').forEach(function (el) {
      if (el.closest('.stagger-group')) return;
      gsap.from(el, {
        y: 60,
        opacity: 0,
        duration: 1.2,
        ease: 'power4.out',
        clearProps: 'all',
        scrollTrigger: {
          trigger: el,
          start: 'top 88%',
          once: true
        }
      });
    });

    /* ============================================
       6) SCRUB EFFECTS — scroll se 1:1 linked
       ============================================ */

    // Comparison table float
    var cmpTable = document.querySelector('.compare-table-wrap');
    if (cmpTable) {
      gsap.fromTo(cmpTable,
        { y: 40 },
        {
          y: -40,
          ease: 'none',
          scrollTrigger: {
            trigger: cmpTable,
            start: 'top bottom',
            end: 'bottom top',
            scrub: 1
          }
        });
    }

    // Process number badges rotate on scroll
    gsap.utils.toArray('.process-num').forEach(function (num) {
      gsap.from(num, {
        rotateZ: -180,
        scale: 0.3,
        ease: 'none',
        scrollTrigger: {
          trigger: num,
          start: 'top 95%',
          end: 'top 55%',
          scrub: 1
        }
      });
    });

    // Final CTA zoom-settle
    var cta = document.querySelector('.final-cta-card');
    if (cta) {
      gsap.fromTo(cta,
        { scale: 0.93, opacity: 0.4 },
        {
          scale: 1, opacity: 1,
          ease: 'none',
          scrollTrigger: {
            trigger: cta,
            start: 'top 95%',
            end: 'top 45%',
            scrub: 0.8
          }
        });
    }

    /* ============================================
       7) Refresh after full page load
       ============================================ */
    window.addEventListener('load', function () {
      ScrollTrigger.refresh();
    });

  });
})();