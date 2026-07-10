//3D Interactive Mouse Parallax Engine (legacy hero stage)
// Guarded: the #viewport3d stage was replaced by the hero product carousel,
// so this only runs if those elements still exist on the page.
const viewport = document.getElementById('viewport3d');
const transformer = document.getElementById('transformer3d');

if (viewport && transformer) {
    viewport.addEventListener('mousemove', (e) => {
        const rect = viewport.getBoundingClientRect();

        // Getting coordinates from middle center point (0,0)
        const x = e.clientX - rect.left - (rect.width / 2);
        const y = e.clientY - rect.top - (rect.height / 2);

        // Calculate rotational tilt angels max limits 15 deg
        const degX = (-y / (rect.height / 2)) * 14;
        const degY = (x / (rect.width / 2)) * 14;

        transformer.style.transform = `rotateX(${degX}deg) rotateY(${degY}deg)`;
    });

    // Reset stage position cleanly on mouse leave
    viewport.addEventListener('mouseleave', () => {
        transformer.style.transform = 'rotateX(0deg) rotateY(0deg)';
    });
}

// =====================
// Savings Calculators (Rolls / Ink / Powder) + WhatsApp catalog request
// =====================
(function () {
    const formatINR = (n) => '₹' + (Math.round(Number(n) || 0)).toLocaleString('en-IN');

    const cards = document.querySelectorAll('.calc3-card');
    const totalEl = document.getElementById('calcTotal');

    function recalcCard(card) {
        const other = Number(card.querySelector('.c-other').value) || 0;
        const kas = Number(card.querySelector('.c-kasauti').value) || 0;
        const qty = Number(card.querySelector('.c-qty').value) || 0;

        const otherCost = other * qty;
        const kasCost = kas * qty;
        const save = Math.max(otherCost - kasCost, 0);
        const pct = otherCost > 0
            ? Math.max(0, Math.min(100, (otherCost - kasCost) / otherCost * 100))
            : 0;

        card.querySelector('.c-save').textContent = formatINR(save);
        card.querySelector('.c-bar-fill').style.width = pct + '%';
        card.querySelector('.c-pct').textContent = pct.toFixed(1) + '% cheaper';
        return save;
    }

    function recalcAll() {
        let total = 0;
        cards.forEach((c) => { total += recalcCard(c); });
        if (totalEl) totalEl.textContent = formatINR(total);
    }

    if (cards.length) {
        cards.forEach((card) => {
            card.querySelectorAll('input').forEach((inp) => {
                ['input', 'change'].forEach((evt) => inp.addEventListener(evt, recalcAll));
            });
        });
        recalcAll();
    }

    // ---- WhatsApp catalog request ----
    const form = document.getElementById('catalogForm');
    if (form) {
        const numberInput = document.getElementById('catalogNumber');
        const msg = document.getElementById('catalogMsg');
        const btn = document.getElementById('catalogSubmit');
        const cfg = window.KASAUTI_CATALOG || {};

        function showMsg(text, ok) {
            if (!msg) return;
            msg.textContent = text;
            msg.className = 'wa-msg ' + (ok ? 'ok' : 'err');
        }

        // Keep digits only as the user types
        numberInput.addEventListener('input', () => {
            numberInput.value = numberInput.value.replace(/[^\d]/g, '').slice(0, 15);
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const digits = (numberInput.value || '').replace(/\D/g, '');
            if (digits.length < 10) {
                showMsg('Please enter a valid WhatsApp number.', false);
                return;
            }
            // Default +91 for a standard 10-digit Indian mobile number
            const number = digits.length === 10 ? ('+91 ' + digits) : ('+' + digits);

            btn.disabled = true;
            btn.classList.add('is-loading');
            try {
                const body = new URLSearchParams({
                    whatsapp_number: number,
                    note: 'Home savings calculator',
                });
                const res = await fetch(cfg.url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': cfg.csrf || '',
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: body.toString(),
                });
                const data = await res.json().catch(() => ({}));
                if (res.ok && data.ok) {
                    showMsg(data.message || 'Thanks! We will message you on WhatsApp shortly.', true);
                    form.reset();
                } else {
                    showMsg((data && data.error) || 'Something went wrong. Please try again.', false);
                }
            } catch (err) {
                showMsg('Network error. Please try again.', false);
            } finally {
                btn.disabled = false;
                btn.classList.remove('is-loading');
            }
        });
    }
})();

// =====================
// Verified Reviews Carousel (3D + auto sliding)
// =====================
(function () {
    const track = document.getElementById('reviewTrack');
    const carousel = document.getElementById('reviewsCarousel');
    if (!track || !carousel) return;

    const prevBtn = carousel.querySelector('.rc-nav.prev');
    const nextBtn = carousel.querySelector('.rc-nav.next');
    const cards = Array.from(track.querySelectorAll('.rc-card'));

    let index = 0;
    let timer = null;
    let step = 1;

    function calcStep() {
        // For responsive layout: show roughly 3 on desktop, 2 on tablet, 1 on mobile.
        const w = window.innerWidth;
        if (w <= 575) return 1;
        if (w <= 991) return 2;
        return 3;
    }

    function update3d() {
        // Simple 3D effect: bring active cards forward based on index.
        cards.forEach((card, i) => {
            const dist = i - index;
            const abs = Math.abs(dist);
            const z = Math.max(60 - abs * 18, 0);
            const r = Math.max(10 - abs * 2.5, 0);
            card.style.transform = `translateZ(${z}px) rotateY(${dist * -3}deg) scale(${abs === 0 ? 1.02 : 0.98})`;
            card.style.opacity = abs > 3 ? '0.65' : '1';
            card.style.filter = abs === 0 ? 'saturate(1.1)' : 'saturate(1)';
        });
    }

    function getCardWidthWithGap() {
        if (!cards.length) return 0;
        const card = cards[0];
        const rect = card.getBoundingClientRect();
        const styles = window.getComputedStyle(track);
        // gap is defined on track via CSS, but computedStyle.gap is reliable.
        const gap = parseFloat(getComputedStyle(track).gap || '0');
        return rect.width + gap;
    }

    function render() {
        step = calcStep();
        const unit = getCardWidthWithGap();
        const maxIndex = Math.max(0, cards.length - step);
        index = Math.max(0, Math.min(index, maxIndex));

        track.style.transform = `translateX(${-index * unit}px)`;
        update3d();
    }

    function next() {
        index += step;
        if (index >= cards.length) index = 0;
        render();
    }

    function prev() {
        index -= step;
        if (index < 0) {
            index = Math.max(0, cards.length - step);
        }
        render();
    }

    if (nextBtn) nextBtn.addEventListener('click', () => {
        if (timer) clearInterval(timer);
        next();
        start();
    });

    if (prevBtn) prevBtn.addEventListener('click', () => {
        if (timer) clearInterval(timer);
        prev();
        start();
    });

    function start() {
        if (timer) clearInterval(timer);
        timer = setInterval(next, 3800);
    }

    // Pause on hover
    carousel.addEventListener('mouseenter', () => {
        if (timer) clearInterval(timer);
    });
    carousel.addEventListener('mouseleave', start);

    window.addEventListener('resize', () => render());

    // Touch / mouse swipe support — gives a manual "slide" option on mobile
    // (where the arrow buttons are hidden by CSS).
    var swStartX = 0, swDelta = 0, swiping = false;
    var swArea = carousel.querySelector('.rc-viewport') || carousel;
    function swStart(x) { swStartX = x; swDelta = 0; swiping = true; if (timer) clearInterval(timer); }
    function swMove(x) { if (swiping) swDelta = x - swStartX; }
    function swEnd() {
        if (!swiping) return;
        swiping = false;
        if (swDelta < -45) next();
        else if (swDelta > 45) prev();
        start();
    }
    swArea.addEventListener('touchstart', function (e) { swStart(e.touches[0].clientX); }, { passive: true });
    swArea.addEventListener('touchmove', function (e) { swMove(e.touches[0].clientX); }, { passive: true });
    swArea.addEventListener('touchend', swEnd);
    swArea.addEventListener('mousedown', function (e) { e.preventDefault(); swStart(e.clientX); });
    window.addEventListener('mousemove', function (e) { swMove(e.clientX); });
    window.addEventListener('mouseup', swEnd);

    render();
    start();
})();
// ==============================
// Faqs section
// ================================
(function () {
    const root = document.querySelector('.faq-section');
    if (!root) return;

    const items = Array.from(root.querySelectorAll('.faq-item'));
    const setOpen = (item, open) => {
        const btn = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        if (!btn || !answer) return;

        if (open) {
            const inner = item.querySelector('.faq-answer-inner');
            const targetH = inner ? inner.scrollHeight : answer.scrollHeight;
            answer.style.height = targetH + 'px';
            item.dataset.open = 'true';
            btn.setAttribute('aria-expanded', 'true');
            answer.setAttribute('aria-hidden', 'false');
        } else {
            answer.style.height = '0px';
            item.dataset.open = 'false';
            btn.setAttribute('aria-expanded', 'false');
            answer.setAttribute('aria-hidden', 'true');
        }
    };

    // initialize closed
    items.forEach(item => {
        const btn = item.querySelector('.faq-question');
        const answer = item.querySelector('.faq-answer');
        if (!btn || !answer) return;
        item.dataset.open = 'false';
        btn.setAttribute('aria-expanded', 'false');
        answer.style.height = '0px';
        answer.setAttribute('aria-hidden', 'true');
    });

    items.forEach(item => {
        const btn = item.querySelector('.faq-question');
        if (!btn) return;

        btn.addEventListener('click', () => {
            const isOpen = item.dataset.open === 'true';

            // allow multiple? requirement says hide/collapse; keep it single-open for cleaner UX
            items.forEach(other => {
                if (other === item) return;
                if (other.dataset.open === 'true') setOpen(other, false);
            });

            setOpen(item, !isOpen);
        });
    });

    // fix heights on resize if open
    window.addEventListener('resize', () => {
        items.forEach(item => {
            if (item.dataset.open !== 'true') return;
            const inner = item.querySelector('.faq-answer-inner');
            const answer = item.querySelector('.faq-answer');
            if (!inner || !answer) return;
            answer.style.height = inner.scrollHeight + 'px';
        });
    });
})();
