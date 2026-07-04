# KASAUTI INTERNATIONAL LLP — Django Backend (v2 — All Fixes Applied)

---

## Bugs Fixed in This Version

| # | Issue | Fix |
|---|-------|-----|
| 1 | Login/Register giving 403 CSRF error | Added `@ensure_csrf_cookie` decorator; fixed `.container.active` CSS conflict with Bootstrap by renaming to `.login-container.active`; login.js updated to match |
| 2 | Order can be placed without login | `@login_required` on checkout view; Django auto-redirects to `/login/?next=/checkout/` |
| 3 | Logout in navbar + no profile page | Logout removed from navbar; `profile/` page added with user info, order history, and logout button |
| 4 | NoneType error opening order in admin | Fixed `OrderItemInline` — `line_total` is a Python property, not a DB field; replaced with safe `display_line_total()` method with None guards |
| 5 | Add to Cart / Buy Now works without login | JS checks `IS_LOGGED_IN` flag; redirects to login page if not authenticated |
| 6 | Cart/Clear Cart visible to guests | Cart button and Clear Cart hidden when not logged in; `loadCart()` returns empty for guests |
| 7 | Other bugs | Fixed broken HTML in `home.html` (broken `<span>` tag); fixed address typo in `contact.html`; fixed duplicate `id="hadding"` in login.html (changed to class); `line_total` property now guards against None |

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Create database tables
python manage.py migrate

# 3. Seed products into DB (same 4 products as the frontend)
python manage.py seed_products

# 4. Create admin user
python manage.py createsuperuser

# 5. Run server
python manage.py runserver
```

Open: **http://127.0.0.1:8000/**
Admin: **http://127.0.0.1:8000/admin/**

---

## Pages & URLs

| URL | Page | Auth Required |
|-----|------|--------------|
| `/` | Home | No |
| `/about/` | About | No |
| `/products/` | Products + Cart | No (but cart/checkout needs login) |
| `/contact/` | Contact form | No |
| `/login/` | Login & Register | No (redirects to profile if already logged in) |
| `/logout/` | Logout | — |
| `/profile/` | Profile + My Orders + Logout | Yes |
| `/checkout/` | Checkout | Yes |
| `/order/success/<id>/` | Order Success | — |
| `/admin/` | Django Admin | Superuser |

---

## Project Structure

```
kasauti_project/
├── manage.py
├── requirements.txt
├── kasauti_project/       # Settings
│   ├── settings.py
│   └── urls.py
├── core/                  # Main app
│   ├── models.py          # Product, ContactInquiry, CartItem, Order, OrderItem
│   ├── views.py           # All views + JSON cart API
│   ├── urls.py            # Routes
│   ├── forms.py           # All forms
│   ├── admin.py           # Admin config
│   └── management/commands/seed_products.py
├── templates/             # All HTML
│   ├── base.html          # Navbar (profile button when logged in)
│   ├── home.html       # Home
│   ├── product.html       # Products + cart
│   ├── login.html         # Login & Register
│   ├── profile.html       # Profile + orders + logout
│   ├── checkout.html      # Checkout
│   ├── contact.html       # Contact form
│   ├── about.html         # About
│   └── order_success.html
└── static/
    ├── css/               # All CSS including profile.css (new)
    ├── js/                # product.js (login-gated), login.js (fixed)
    └── image/             # All images
```

---

## Production Checklist

Before going live, update `settings.py`:
1. `SECRET_KEY` → use a long random string or env var
2. `DEBUG = False`
3. `ALLOWED_HOSTS` → your domain
4. Switch `EMAIL_BACKEND` to SMTP
5. Run `python manage.py collectstatic`
6. Use PostgreSQL for production database

Test Auto Deploy done