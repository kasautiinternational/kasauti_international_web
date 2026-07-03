document.addEventListener("DOMContentLoaded", function () {

    let currentPath = window.location.pathname;

    // Navbar Links
    document.querySelectorAll(".nav-link").forEach(link => {

        let href = link.getAttribute("href");

        if (href && href !== "#" && href === currentPath) {
            link.classList.add("active");
        }
    })

});
// footer
(function () {
  function bindTilt(selector) {
    const els = document.querySelectorAll(selector);
    els.forEach((el) => {
      el.addEventListener('mousemove', (e) => {
        const rect = el.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        el.style.setProperty('--fx', `${x}%`);
        el.style.setProperty('--fy', `${y}%`);
        el.style.setProperty('--sx', `${x}%`);
        el.style.setProperty('--sy', `${y}%`);
      });
    });
  }

  // Footer 3D glow position
  bindTilt('.footer-col');
  bindTilt('.social-link');

  // Reduce motion support
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.footer-col, .social-link').forEach((el) => {
      el.style.removeProperty('--fx');
      el.style.removeProperty('--fy');
      el.style.removeProperty('--sx');
      el.style.removeProperty('--sy');
    });
  }
})();


// Navbar scroll-shrink — adds .kas-scrolled once the page is scrolled a little
(function () {
    const nav = document.querySelector('.custom-navbar');
    if (!nav) return;
    const THRESHOLD = 30;
    let ticking = false;
    function update() {
        nav.classList.toggle('kas-scrolled', window.scrollY > THRESHOLD);
        ticking = false;
    }
    window.addEventListener('scroll', function () {
        if (!ticking) {
            window.requestAnimationFrame(update);
            ticking = true;
        }
    }, { passive: true });
    update(); // initial state (handles reloads while already scrolled)
})();
