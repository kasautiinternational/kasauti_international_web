/* ============================================================
   Kasauti International — Hero Product Carousel
   3D coverflow showcase that replaces the old hero machine stage.
   Features: center/side depth layout, auto-scroll (3s), pause on
   hover, resume after manual interaction, arrows, dots, keyboard
   and touch-swipe support. Respects prefers-reduced-motion.
   ============================================================ */
(function () {
    const root = document.getElementById('heroCarousel');
    if (!root) return;

    const track = root.querySelector('#hcTrack');
    const cards = Array.from(root.querySelectorAll('.hc-card'));
    const prevBtn = root.querySelector('.hc-prev');
    const nextBtn = root.querySelector('.hc-next');
    const dotsWrap = root.querySelector('#hcDots');
    const catEl = root.querySelector('#hcCat');
    const subEl = root.querySelector('#hcSub');
    if (!track || cards.length === 0) return;

    const AUTO_MS = 3000;     // auto-advance every 3 seconds
    const RESUME_MS = 6000;   // resume auto-scroll 6s after a manual action
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let current = 0;
    let animating = false;
    let autoTimer = null;
    let resumeTimer = null;

    // Build dots from the number of cards
    const dots = cards.map((_, i) => {
        const d = document.createElement('button');
        d.type = 'button';
        d.className = 'hc-dot' + (i === 0 ? ' active' : '');
        d.setAttribute('aria-label', 'Go to product ' + (i + 1));
        d.addEventListener('click', () => poke(() => render(i)));
        dotsWrap && dotsWrap.appendChild(d);
        return d;
    });

    function render(index) {
        if (animating) return;
        animating = true;
        current = (index + cards.length) % cards.length;

        cards.forEach((card, i) => {
            const offset = (i - current + cards.length) % cards.length;
            card.classList.remove('center', 'left-1', 'left-2', 'right-1', 'right-2', 'hidden');
            if (offset === 0) card.classList.add('center');
            else if (offset === 1) card.classList.add('right-1');
            else if (offset === 2) card.classList.add('right-2');
            else if (offset === cards.length - 1) card.classList.add('left-1');
            else if (offset === cards.length - 2) card.classList.add('left-2');
            else card.classList.add('hidden');
        });

        dots.forEach((d, i) => d.classList.toggle('active', i === current));

        // Fade the caption in/out
        const active = cards[current];
        const cat = active.getAttribute('data-cat') || '';
        const sub = active.getAttribute('data-sub') || '';
        if (catEl && subEl) {
            catEl.style.opacity = '0';
            subEl.style.opacity = '0';
            setTimeout(() => {
                catEl.textContent = cat;
                subEl.textContent = sub;
                catEl.style.opacity = '1';
                subEl.style.opacity = '1';
            }, 250);
        }

        setTimeout(() => { animating = false; }, 700);
    }

    function next() { render(current + 1); }
    function prev() { render(current - 1); }

    function startAuto() {
        if (reduceMotion) return;
        stopAuto();
        autoTimer = setInterval(next, AUTO_MS);
    }
    function stopAuto() {
        if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
    }
    // Run an action triggered by the user, then resume auto-scroll later
    function poke(fn) {
        stopAuto();
        fn();
        if (resumeTimer) clearTimeout(resumeTimer);
        resumeTimer = setTimeout(startAuto, RESUME_MS);
    }

    // Controls
    nextBtn && nextBtn.addEventListener('click', () => poke(next));
    prevBtn && prevBtn.addEventListener('click', () => poke(prev));

    // Clicking a side card brings it to the centre instead of navigating away.
    cards.forEach((card, i) => {
        card.addEventListener('click', (e) => {
            if (!card.classList.contains('center')) {
                e.preventDefault();
                poke(() => render(i));
            }
        });
    });

    // Pause on hover, resume on leave
    root.addEventListener('mouseenter', stopAuto);
    root.addEventListener('mouseleave', startAuto);

    // Keyboard (only when the carousel area is hovered/focused within)
    root.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') poke(prev);
        else if (e.key === 'ArrowRight') poke(next);
    });

    // Touch swipe
    let startX = 0;
    root.addEventListener('touchstart', (e) => { startX = e.changedTouches[0].screenX; }, { passive: true });
    root.addEventListener('touchend', (e) => {
        const diff = startX - e.changedTouches[0].screenX;
        if (Math.abs(diff) > 50) poke(() => (diff > 0 ? next() : prev()));
    }, { passive: true });

    // Init
    render(0);
    startAuto();
})();

// =====================
// Reels Carousel (arrows + dots + swipe). Videos auto-play (muted).
// Play btn = sound ON (baaki sab mute). Pause btn = sound OFF,
// video muted autoplay me chalti rehti hai.
// =====================


(function () {
    function initReels() {
        var carousel = document.getElementById('reelsCarousel');
        if (!carousel || carousel.dataset.reelsReady === '1') return;

        var track = document.getElementById('reelsTrack');
        var wrap = carousel.querySelector('.reels-track-wrap');
        if (!track || !wrap) return;
        carousel.dataset.reelsReady = '1';

        // Replace arrow buttons with clean clones to strip any stale/broken click handlers.
        function fresh(el) { if (!el || !el.parentNode) return el; var c = el.cloneNode(true); el.parentNode.replaceChild(c, el); return c; }
        var prev = fresh(document.getElementById('reelsPrev'));
        var next = fresh(document.getElementById('reelsNext'));
        var dotsWrap = document.getElementById('reelsDots');

        var cards = Array.prototype.slice.call(track.querySelectorAll('.reel-card'));
        if (!cards.length) return;

        // One "card step" = distance from card 0 to card 1 (includes the gap).
        function step() {
            if (cards.length > 1) {
                var d = Math.abs(cards[1].getBoundingClientRect().left - cards[0].getBoundingClientRect().left);
                if (d > 0) return d;
            }
            return cards[0].offsetWidth + 16;
        }
        function maxScroll() { return wrap.scrollWidth - wrap.clientWidth; }
        function canScroll() { return maxScroll() > 2; }

        if (next) next.addEventListener('click', function (e) { e.preventDefault(); wrap.scrollBy({ left: step(), behavior: 'smooth' }); bump(); });
        if (prev) prev.addEventListener('click', function (e) { e.preventDefault(); wrap.scrollBy({ left: -step(), behavior: 'smooth' }); bump(); });

        // Drag / swipe — pointer events cover both mouse and touch.
        var down = false, startX = 0, startScroll = 0, moved = false;
        wrap.addEventListener('pointerdown', function (e) {
            down = true; moved = false; dragging = true;
            startX = e.clientX; startScroll = wrap.scrollLeft;
            wrap.classList.add('is-dragging');
        });
        window.addEventListener('pointermove', function (e) {
            if (!down) return;
            var dx = e.clientX - startX;
            if (Math.abs(dx) > 4) moved = true;
            wrap.scrollLeft = startScroll - dx;
        });
        function endDrag() { if (!down) return; down = false; dragging = false; wrap.classList.remove('is-dragging'); bump(); }
        window.addEventListener('pointerup', endDrag);
        window.addEventListener('pointercancel', endDrag);
        // Swallow the click that ends a drag so a card doesn't navigate mid-swipe.
        track.addEventListener('click', function (e) { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);

        // Build the pagination dots.
        if (dotsWrap) {
            dotsWrap.innerHTML = '';
            var dots = cards.map(function (_, i) {
                var b = document.createElement('button');
                b.type = 'button';
                b.className = 'reels-dot';
                b.setAttribute('aria-label', 'Go to video ' + (i + 1));
                b.addEventListener('click', function () { wrap.scrollTo({ left: step() * i, behavior: 'smooth' }); bump(); });
                dotsWrap.appendChild(b);
                return b;
            });
            var sync = function () {
                var idx = Math.round(wrap.scrollLeft / step());
                if (idx < 0) idx = 0;
                if (idx > dots.length - 1) idx = dots.length - 1;
                dots.forEach(function (d, i) { d.classList.toggle('is-active', i === idx); });
            };
            var raf;
            wrap.addEventListener('scroll', function () { cancelAnimationFrame(raf); raf = requestAnimationFrame(sync); });
            sync();
        }

        /* ---------- Auto-scroll ---------- */
        var AUTOPLAY_MS = 3500;                 // gap between auto-advances (ms)
        var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var timer = null, hovering = false, dragging = false, hidden = false;

        // NOTE: jab kisi reel ka sound ON hai (has-sound class), auto-scroll pause rahega
        function isPaused() { return hovering || dragging || hidden || reduceMotion || carousel.classList.contains('has-sound'); }
        function autoNext() {
            if (!canScroll()) return;
            if (wrap.scrollLeft >= maxScroll() - 2) {          // reached the end -> loop back to start
                wrap.scrollTo({ left: 0, behavior: 'smooth' });
            } else {
                wrap.scrollBy({ left: step(), behavior: 'smooth' });
            }
        }
        function start() { stop(); if (reduceMotion) return; timer = window.setInterval(function () { if (!isPaused()) autoNext(); }, AUTOPLAY_MS); }
        function stop() { if (timer) { clearInterval(timer); timer = null; } }
        function bump() { if (timer) start(); }              // restart the countdown after any manual action

        carousel.addEventListener('mouseenter', function () { hovering = true; });   // pause on hover (desktop)
        carousel.addEventListener('mouseleave', function () { hovering = false; });
        document.addEventListener('visibilitychange', function () { hidden = document.hidden; }); // pause when tab hidden

        start();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initReels);
    else initReels();
})();


// =====================
// Reel Sound Toggle — videos hamesha muted autoplay chalti rahengi.
// Play btn click = sound ON (baaki sab reels mute ho jayengi).
// Pause btn click = sound OFF, video muted autoplay me chalti rahegi.
// =====================
(function () {
    function initReelSound() {
        var carousel = document.getElementById('reelsCarousel');
        if (!carousel || carousel.dataset.soundReady === '1') return;
        carousel.dataset.soundReady = '1';

        var cards = carousel.querySelectorAll('.reel-card');

        function muteAll() {
            cards.forEach(function (c) {
                var v = c.querySelector('.reel-video');
                if (!v) return;
                v.muted = true;
                v.play().catch(function () { });
                c.classList.remove('reel-playing');
            });
            carousel.classList.remove('has-sound');
        }

        cards.forEach(function (card) {
            var video = card.querySelector('.reel-video');
            var btn = card.querySelector('.reel-sound-btn');
            if (!video || !btn) return;

            function toggleSound(e) {
                e.preventDefault();
                e.stopPropagation();

                if (video.muted) {
                    // Sound ON — pehle baaki sab mute karo
                    muteAll();
                    video.muted = false;
                    video.currentTime = 0; // shuru se sound ke saath; wahi se continue chahiye to ye line hata do
                    video.play().catch(function () { });
                    card.classList.add('reel-playing');
                    carousel.classList.add('has-sound');
                } else {
                    // Sound OFF — video muted autoplay me chalti rahegi
                    video.muted = true;
                    video.play().catch(function () { });
                    card.classList.remove('reel-playing');
                    carousel.classList.remove('has-sound');
                }
            }

            btn.addEventListener('click', toggleSound);
            video.addEventListener('click', toggleSound); // video pe direct click bhi kaam kare
        });

        // Tab hide/switch hone pe sound band ho jaye
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) muteAll();
        });
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initReelSound);
    else initReelSound();
})();


// Stats Counter — runs once when section enters viewport
(function () {
    var statNumbers = document.querySelectorAll('.stat-number');
    if (!statNumbers.length) return;

    function animateCount(el) {
        var target = parseInt(el.getAttribute('data-count'), 10) || 0;
        var duration = 1400;
        var start = null;

        function step(timestamp) {
            if (!start) start = timestamp;
            var progress = Math.min((timestamp - start) / duration, 1);
            el.textContent = Math.floor(progress * target);
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                el.textContent = target;
            }
        }
        requestAnimationFrame(step);
    }

    var statsSection = document.querySelector('.stats-section');
    if (!statsSection) return;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                statNumbers.forEach(animateCount);
                observer.disconnect();
            }
        });
    }, { threshold: 0.3 });

    observer.observe(statsSection);
})();