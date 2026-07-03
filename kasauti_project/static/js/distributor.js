// Lightweight parallax for 3D feel
(function () {
    const stage = document.querySelector('.stage');
    const orbs = stage ? stage.querySelectorAll('.orb') : [];
    const cube = stage ? stage.querySelector('.cube-wrap') : null;

    if (!stage) return;

    // Respect reduced motion
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) return;

    stage.addEventListener('mousemove', (e) => {
        const r = stage.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width;
        const y = (e.clientY - r.top) / r.height;
        const rx = (y - 0.5) * -16;
        const ry = (x - 0.5) * 22;

        stage.style.setProperty('--rx', rx.toFixed(2) + 'deg');
        stage.style.setProperty('--ry', ry.toFixed(2) + 'deg');

        orbs.forEach((orb, i) => {
            const depth = (i + 1) * 8;
            orb.style.transform = `translate3d(${(x - 0.5) * depth}px, ${(y - 0.5) * depth}px, 0)`;
        });

        if (cube) {
            cube.style.transform = `translate3d(0,0,0) rotateX(${rx}deg) rotateY(${ry}deg)`;
        }
    });

    stage.addEventListener('mouseleave', () => {
        stage.style.setProperty('--rx', '0deg');
        stage.style.setProperty('--ry', '0deg');
        orbs.forEach((orb) => (orb.style.transform = 'translate3d(0,0,0)'));
        if (cube) cube.style.transform = '';
    });
})();
