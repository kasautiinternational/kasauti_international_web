// Kasauti Privacy & Policy page JS
// - Left sidebar “Quick Sections” links should open the related accordion section
// - Hash navigation also supported (e.g. /p-and-p#cookies)

(function () {
  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  ready(function () {
    const acc = document.querySelector('[data-pp-accordion]');
    if (!acc) return;

    const buttons = Array.from(acc.querySelectorAll('.pp-accordion-btn'));

    function closeAll(exceptBtn) {
      buttons.forEach((b) => {
        if (exceptBtn && b === exceptBtn) return;
        b.setAttribute('aria-expanded', 'false');
        const panelId = b.getAttribute('aria-controls');
        const panel = panelId ? document.getElementById(panelId) : null;
        if (panel) panel.hidden = true;
      });
    }

    function openByButton(btn) {
      if (!btn) return;
      const isOpen = btn.getAttribute('aria-expanded') === 'true';
      if (!isOpen) {
        closeAll(btn);
        btn.setAttribute('aria-expanded', 'true');
        const panelId = btn.getAttribute('aria-controls');
        const panel = panelId ? document.getElementById(panelId) : null;
        if (panel) panel.hidden = false;
      }
      // If already open, keep it open.
    }

    // Accordion click behavior
    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const panelId = btn.getAttribute('aria-controls');
        const panel = panelId ? document.getElementById(panelId) : null;

        const isOpen = btn.getAttribute('aria-expanded') === 'true';
        if (!isOpen) {
          closeAll(btn);
          btn.setAttribute('aria-expanded', 'true');
          if (panel) panel.hidden = false;
        } else {
          // allow collapse
          btn.setAttribute('aria-expanded', 'false');
          if (panel) panel.hidden = true;
        }
      });
    });

    // Sidebar link behavior
    const toc = acc.parentElement ? null : null; // no-op, just to avoid unused var lint in some setups
    const sidebar = document.querySelector('.pp-sidebar');
    if (sidebar) {
      const links = Array.from(sidebar.querySelectorAll('.pp-toc a[href^="#"]'));

      links.forEach((a) => {
        a.addEventListener('click', (e) => {
          const hash = a.getAttribute('href') || '';
          const id = hash.startsWith('#') ? hash.slice(1) : null;
          if (!id) return;

          e.preventDefault();

          // Open accordion button whose article has id == id
          const sectionArticle = document.getElementById(id);
          const btn = sectionArticle ? sectionArticle.querySelector('.pp-accordion-btn') : null;
          openByButton(btn);

          // Scroll into view after opening (with navbar offset so it doesn't hide under fixed-top navbar)
          const target = sectionArticle || document.getElementById(id);
          const NAV_OFFSET_PX = 180;
          if (target) {
            const rectTop = target.getBoundingClientRect().top;
            // rectTop is relative to the viewport; subtract offset to keep target below navbar
            window.scrollBy({ top: rectTop - NAV_OFFSET_PX, behavior: 'smooth' });
          }


          // Update hash
          history.replaceState(null, '', `#${id}`);
        });
      });
    }

    // Hash deep-link on load
    const hash = (window.location.hash || '').replace('#', '');
    if (hash) {
      const sectionArticle = document.getElementById(hash);
      if (sectionArticle) {
        const btn = sectionArticle.querySelector('.pp-accordion-btn');
        openByButton(btn);
        // don't rely only on default browser behavior; scroll explicitly with navbar offset
        setTimeout(() => {
          const NAV_OFFSET_PX = 140;
          const rectTop = sectionArticle.getBoundingClientRect().top;
          window.scrollBy({ top: rectTop - NAV_OFFSET_PX, behavior: 'smooth' });
        }, 50);

      }
    }
  });
})();

