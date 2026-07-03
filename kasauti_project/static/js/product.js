// ─────────────────────────────────────────────────────
// KASAUTI product.js
// Server-driven cart (source of truth = Django session/DB cart API).
// Works on the landing, category, and product-detail pages.
// Prices & cart are login-gated (Fix 5 & 6) — guests get redirected to login.
// ─────────────────────────────────────────────────────

const API = window.KASAUTI_API || {};
const CSRF = API.csrfToken || '';
const IS_LOGGED_IN = window.KASAUTI_USER_LOGGED_IN === true;
const LOGIN_URL = window.KASAUTI_LOGIN_URL || '/login/?next=/products/';
const FALLBACK_IMG = window.KASAUTI_FALLBACK_IMG || '';

// ─── Helpers ─────────────────────────────────────────

function formatINR(n) {
    return '₹' + Math.round(Number(n) || 0).toLocaleString('en-IN');
}

// Escape values that go inside HTML attributes / text built via innerHTML.
function escAttr(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;').replace(/"/g, '&quot;')
        .replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function gotoLogin() {
    window.location.href = LOGIN_URL;
}

async function apiSend(url, body, method = 'POST') {
    if (!url) return null;
    try {
        const opts = {
            method,
            headers: { 'X-CSRFToken': CSRF },
        };
        if (body !== undefined && body !== null) {
            opts.headers['Content-Type'] = 'application/json';
            opts.body = JSON.stringify(body);
        }
        const res = await fetch(url, opts);
        let data = null;
        try { data = await res.json(); } catch (e) { data = null; }

        // Backend says login required → bounce to login page
        if (res.status === 401 && data && data.redirect) {
            window.location.href = data.redirect;
            return null;
        }
        return data;
    } catch (err) {
        console.warn('Cart API error:', err);
        return null;
    }
}

// ─── Cart rendering (from server) ────────────────────

async function refreshCart() {
    if (!IS_LOGGED_IN) return;
    const data = await apiSend(API.cartDetail, null, 'GET');
    if (data) renderCart(data);
}

function renderCart(data) {
    const countEl = document.getElementById('cartCount');
    if (countEl) countEl.textContent = data.total_items || 0;

    const empty = document.getElementById('cartEmpty');
    const itemsEl = document.getElementById('cartItems');
    const subEl = document.getElementById('cartSubtotal');
    const taxEl = document.getElementById('cartTax');
    const totEl = document.getElementById('cartTotal');

    if (subEl) subEl.textContent = formatINR(data.subtotal);
    if (taxEl) taxEl.textContent = formatINR(data.gst);
    if (totEl) totEl.textContent = formatINR(data.total);

    if (!itemsEl) return;
    itemsEl.innerHTML = '';

    const items = data.items || [];
    if (items.length === 0) {
        if (empty) empty.style.display = 'block';
        return;
    }
    if (empty) empty.style.display = 'none';

    for (const item of items) {
        const row = document.createElement('div');
        row.className = 'cart-item';
        const img = item.img || FALLBACK_IMG;
        const key = escAttr(item.key || item.product_id);
        const title = escAttr(item.title);
        const sizeLine = item.size
            ? `<div class="ci-size">Size: ${escAttr(item.size)} in</div>`
            : '';
        row.innerHTML = `
        <div class="ci-media">
          <img src="${img}" alt="${title}" onerror="this.src='${FALLBACK_IMG}'">
        </div>
        <div class="ci-info">
          <div class="ci-title">${title}</div>
          ${sizeLine}
          <div class="ci-sub">${formatINR(item.price)} • each</div>
          <div class="ci-qty">
            <button class="qty-btn" data-action="dec" data-key="${key}" type="button">-</button>
            <span class="qty">${item.qty}</span>
            <button class="qty-btn" data-action="inc" data-key="${key}" type="button">+</button>
          </div>
        </div>
        <div class="ci-right">
          <div class="ci-total">${formatINR(item.line_total)}</div>
          <button class="trash" data-action="remove" data-key="${key}" type="button" aria-label="Remove">
            <i class="fa-solid fa-trash"></i>
          </button>
        </div>`;
        itemsEl.appendChild(row);
    }
}

// ─── Cart actions ────────────────────────────────────

async function addToCart(id, qty = 1, size = '') {
    if (!IS_LOGGED_IN) { gotoLogin(); return false; }
    const data = await apiSend(API.cartAdd, { product_id: id, qty, size });
    if (data) renderCart(data);
    return !!data;
}

async function changeQty(key, delta, row) {
    if (!IS_LOGGED_IN) { gotoLogin(); return; }
    // Read current qty straight from the clicked row (robust to any size text)
    let current = 1;
    if (row) {
        const q = row.querySelector('.qty');
        current = parseInt(q ? q.textContent : '1', 10) || 1;
    }
    const newQty = current + delta;
    let data;
    if (newQty <= 0) {
        data = await apiSend(API.cartRemove, { key });
    } else {
        data = await apiSend(API.cartUpdate, { key, qty: newQty });
    }
    if (data) renderCart(data);
}

async function removeItem(key) {
    if (!IS_LOGGED_IN) { gotoLogin(); return; }
    const data = await apiSend(API.cartRemove, { key });
    if (data) renderCart(data);
}

async function clearCart() {
    if (!IS_LOGGED_IN) { gotoLogin(); return; }
    const data = await apiSend(API.cartClear, {});
    if (data) renderCart(data);
}

// ─── Notify me (out of stock) ────────────────────────

async function requestNotify(id, btn) {
    if (!IS_LOGGED_IN) { gotoLogin(); return; }
    if (!id || !API.notify) return;
    btn.classList.add('is-loading');
    const data = await apiSend(API.notify, { product_id: id });
    btn.classList.remove('is-loading');
    if (data && data.success) {
        btn.style.display = 'none';
        const done = document.getElementById('notifyDone');
        if (done) done.hidden = false;
    }
}

// ─── Drawer ──────────────────────────────────────────

function openCart() {
    if (!IS_LOGGED_IN) { gotoLogin(); return; }
    const drawer = document.getElementById('cartDrawer');
    if (!drawer) return;
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    refreshCart();
}

function closeCart() {
    const drawer = document.getElementById('cartDrawer');
    if (!drawer) return;
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
}

// ─── Product photo gallery (detail page) ─────────────

function initGallery() {
    const gallery = document.querySelector('[data-gallery]');
    if (!gallery) return;
    const slides = Array.from(gallery.querySelectorAll('.pd-img'));
    const thumbs = Array.from(gallery.querySelectorAll('.pd-thumb'));
    if (slides.length <= 1) return;  // single photo → nothing to slide

    let index = 0;

    function show(i) {
        index = (i + slides.length) % slides.length;  // wrap around
        slides.forEach((s, n) => s.classList.toggle('is-active', n === index));
        thumbs.forEach((t, n) => t.classList.toggle('is-active', n === index));
    }

    // Prev / next arrows
    gallery.querySelectorAll('[data-nav]').forEach(btn => {
        btn.addEventListener('click', () => {
            show(index + (btn.dataset.nav === 'next' ? 1 : -1));
        });
    });

    // Thumbnail clicks
    thumbs.forEach(t => {
        t.addEventListener('click', () => show(parseInt(t.dataset.thumb, 10) || 0));
    });

    // Swipe on touch devices
    const stage = gallery.querySelector('.pd-img-box');
    if (stage) {
        let startX = 0, dragging = false;
        stage.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX; dragging = true;
        }, { passive: true });
        stage.addEventListener('touchend', (e) => {
            if (!dragging) return;
            dragging = false;
            const dx = e.changedTouches[0].clientX - startX;
            if (Math.abs(dx) > 40) show(index + (dx < 0 ? 1 : -1));
        }, { passive: true });
    }
}

// ─── Size selector (detail page) ─────────────────────

function initSizePicker() {
    const box = document.getElementById('pdSize');
    if (!box) return;  // product has no sizes → nothing to wire
    const btns = Array.from(box.querySelectorAll('.pd-size-btn'));
    const hint = document.getElementById('pdSizeHint');

    btns.forEach(b => {
        b.addEventListener('click', () => {
            btns.forEach(x => x.classList.remove('is-selected'));
            b.classList.add('is-selected');
            box.dataset.selected = b.dataset.size || '';
            updatePriceForSize(b);            // price row follows the tapped size
            if (hint) hint.hidden = true;     // clear any "pick a size" prompt
            box.classList.remove('shake');
        });
    });
}

// Update the big price row to match the tapped size (price / MRP / % off).
function updatePriceForSize(btn) {
    if (!btn) return;
    const now = document.getElementById('pdNow');
    const mrp = document.getElementById('pdMrp');
    const off = document.getElementById('pdOff');
    if (now && btn.dataset.sell) now.textContent = formatINR(btn.dataset.sell);
    if (mrp) {
        const m = btn.dataset.mrp;
        if (m) { mrp.textContent = formatINR(m); mrp.hidden = false; }
        else { mrp.hidden = true; }
    }
    if (off) {
        const o = parseInt(btn.dataset.off || '0', 10);
        if (o > 0) { off.textContent = o + '% OFF'; off.hidden = false; }
        else { off.hidden = true; }
    }
}

// Whether this product requires a size, and which one is picked.
function getSelectedSize() {
    const box = document.getElementById('pdSize');
    if (!box) return { required: false, value: '' };
    return { required: true, value: box.dataset.selected || '' };
}

// Prompt the customer to pick a size (inline hint + a short shake).
function flagSizeRequired() {
    const box = document.getElementById('pdSize');
    const hint = document.getElementById('pdSizeHint');
    if (hint) hint.hidden = false;
    if (box) {
        box.classList.remove('shake');
        void box.offsetWidth;  // reflow so the shake can replay
        box.classList.add('shake');
        box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// ─── Wire up ─────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Load current cart count/contents for logged-in users
    refreshCart();

    // Product-detail photo gallery
    initGallery();

    // Product-detail size selector (only does anything if the product has sizes)
    initSizePicker();

    // Hero buttons
    const btnOpen = document.getElementById('btnOpenCart');
    const btnClose = document.getElementById('btnCloseCart');
    const backdrop = document.getElementById('cartBackdrop');
    const btnClear = document.getElementById('btnClearCart');
    const btnCheckout = document.getElementById('btnCheckout');
    const itemsEl = document.getElementById('cartItems');

    if (btnOpen) btnOpen.addEventListener('click', openCart);
    if (btnClose) btnClose.addEventListener('click', closeCart);
    if (backdrop) backdrop.addEventListener('click', closeCart);
    if (btnClear) btnClear.addEventListener('click', clearCart);

    if (btnCheckout) {
        btnCheckout.addEventListener('click', () => {
            if (!IS_LOGGED_IN) { gotoLogin(); return; }
            if (API.checkout) window.location.href = API.checkout;
        });
    }

    // Drawer qty / remove (event delegation)
    if (itemsEl) {
        itemsEl.addEventListener('click', async (e) => {
            const target = e.target.closest('[data-action]');
            if (!target) return;
            const action = target.dataset.action;
            const key = target.dataset.key;
            const row = target.closest('.cart-item');
            if (action === 'inc') await changeQty(key, 1, row);
            else if (action === 'dec') await changeQty(key, -1, row);
            else if (action === 'remove') await removeItem(key);
        });
    }

    // Product-detail page: Add to Cart / Buy Now
    document.querySelectorAll('[data-action="add"], [data-action="buy"]').forEach(btn => {
        // Skip drawer buttons (those live inside #cartItems and are handled above)
        if (btn.closest('#cartItems')) return;
        btn.addEventListener('click', async () => {
            if (!IS_LOGGED_IN) { gotoLogin(); return; }
            const action = btn.dataset.action;
            const id = btn.dataset.id;
            if (!id) return;

            // If this product has size options, one must be selected first.
            const size = getSelectedSize();
            if (size.required && !size.value) {
                flagSizeRequired();
                return;
            }

            btn.classList.add('is-loading');
            const ok = await addToCart(id, 1, size.value);
            btn.classList.remove('is-loading');
            if (!ok) return;
            if (action === 'add') {
                openCart();
            } else if (action === 'buy') {
                if (API.checkout) window.location.href = API.checkout;
                else openCart();
            }
        });
    });

    // Product-detail page: Notify Me (out of stock)
    const btnNotify = document.getElementById('btnNotify');
    if (btnNotify) {
        btnNotify.addEventListener('click', () => requestNotify(btnNotify.dataset.id, btnNotify));
    }
});
