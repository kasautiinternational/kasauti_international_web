import json
import os
import re
import random
import mimetypes
from decimal import Decimal
from datetime import datetime, timedelta

from django.utils import timezone
from django.core.mail import send_mail

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse, FileResponse, StreamingHttpResponse, HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import (
    Product, ContactInquiry, CartItem, Order, OrderItem,
    CustomerReview, ReelVideo, DistributorInquiry, StockNotification, CatalogRequest,
)
from .forms import LoginForm, RegisterForm, ContactForm, CheckoutForm, ProfileForm, DistributorForm


# ─────────────────────────────────────────
# Public pages
# ─────────────────────────────────────────

def about(request):
    return render(request, 'about.html')

def distributor(request):
    """Distributor page — saves distributor applications to the DB."""
    if request.method == 'POST':
        form = DistributorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you! Your distributor application has been received. "
                "Our team will contact you soon."
            )
            return redirect('/distributor/#apply')
        else:
            messages.error(request, "Please fill all fields correctly and try again.")
    else:
        form = DistributorForm()
    return render(request, 'distributor.html', {'form': form})

def privacy_policy(request):
    return render(request,'privacy_policy.html')

def terms_condition(request):
    return render(request,'terms_condition.html')

def refund_return(request):
    return render(request,'refund_return.html')

def shipping_policy(request):
    return render(request,'shipping_policy.html')

def services(request):
    return render(request,'services.html')

# ─────────────────────────────────────────
# Email OTP helpers (registration verification)
# ─────────────────────────────────────────
OTP_VALIDITY_MINUTES = 10      # code kitne minute valid rahega
OTP_MAX_ATTEMPTS = 5           # kitni galat koshish allowed


def _generate_otp():
    """6-digit numeric OTP as a string (e.g. '048273')."""
    return f"{random.randint(0, 999999):06d}"


def _mask_email(email):
    """rahul@gmail.com -> ra***@gmail.com  (privacy on the OTP screen)."""
    try:
        name, domain = email.split('@', 1)
    except ValueError:
        return email
    if len(name) <= 2:
        masked = name[:1] + '*'
    else:
        masked = name[:2] + '*' * (len(name) - 2)
    return f"{masked}@{domain}"


def _send_registration_otp(email, otp, username):
    """Send the 6-digit OTP (plain-text + branded HTML) to the user."""
    subject = "Your Kasauti International verification code"
    text_body = (
        f"Hi {username},\n\n"
        f"Your OTP for Kasauti International registration is: {otp}\n\n"
        f"Yeh code {OTP_VALIDITY_MINUTES} minute ke liye valid hai. "
        "Ise kisi ke saath share na karein.\n\n"
        "Agar aapne registration nahi kiya to is email ko ignore karein.\n\n"
        "Regards,\nTeam Kasauti International"
    )
    html_body = f"""
<div style="margin:0;padding:0;background:#faf9f6;font-family:'Poppins',Arial,sans-serif;">
  <div style="max-width:520px;margin:0 auto;padding:32px 20px;">
    <div style="height:6px;border-radius:6px;overflow:hidden;display:flex;margin-bottom:24px;">
      <span style="flex:1;background:#06b6d4;">&nbsp;</span>
      <span style="flex:1;background:#e0529c;">&nbsp;</span>
      <span style="flex:1;background:#eab308;">&nbsp;</span>
      <span style="flex:1;background:#7c3aed;">&nbsp;</span>
    </div>
    <div style="background:#ffffff;border:1px solid rgba(201,151,63,0.18);border-radius:18px;padding:32px 28px;box-shadow:0 20px 60px rgba(15,23,42,0.08);">
      <h1 style="margin:0 0 4px;font-size:20px;color:#0f172a;font-weight:700;">Kasauti International</h1>
      <p style="margin:0 0 24px;font-size:13px;color:#94a3b8;">Email Verification</p>
      <p style="margin:0 0 8px;font-size:15px;color:#0f172a;">Hi <b>{username}</b>,</p>
      <p style="margin:0 0 24px;font-size:14px;color:#475569;line-height:1.6;">
        Welcome! Please use the verification code below to verify your email and activate your account:
      </p>
      <div style="text-align:center;margin:0 0 24px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#c9973f,#f5d08a);color:#ffffff;font-size:34px;font-weight:700;letter-spacing:10px;padding:16px 26px 16px 36px;border-radius:14px;">
          {otp}
        </div>
      </div>
      <p style="margin:0 0 6px;font-size:13px;color:#94a3b8;text-align:center;">
        This verification code is valid for {OTP_VALIDITY_MINUTES} minutes.
      </p>
      <p style="margin:0;font-size:15px;color:#000000;text-align:center;">
        Ise kisi ke saath share na karein. Agar aapne request nahi kiya to email ignore karein.
      </p>
    </div>
    <p style="text-align:center;margin:20px 0 0;font-size:11px;color:#3d077b;">
      © Kasauti International LLP • Noida, India
    </p>
  </div>
</div>
"""
    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_body,
        fail_silently=False,
    )


def _send_welcome_email(email, username):
    """Optional welcome mail after successful verification (non-blocking)."""
    try:
        send_mail(
            subject="Welcome to Kasauti International!",
            message=(
                    f"Dear {username},\n\n"
                        "Congratulations! Your Kasauti International account has been created successfully.\n\n"
                        "You can now log in to your account to explore our complete range of premium DTF printing supplies, "
                        "including DTF Inks, PET Film Rolls, Hot Melt Powder, Sublimation Papers, and other products. "
                        "You can also place orders, request quotations, and stay updated with our latest products and offers.\n\n"
                        "We are committed to providing high-quality products, competitive pricing, and reliable customer support "
                        "to help your business grow.\n\n"
                        "If you have any questions or need assistance, our team is always happy to help.\n\n"
                        "Thank you for choosing Kasauti International. We look forward to serving you.\n\n"
                        "Best Regards,\n"
                        "Team Kasauti International"
                    ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass


# ─────────────────────────────────────────
# Forgot Password (email OTP → new password)
# Login page ka modal in 3 JSON endpoints ko call karta hai:
#   1) /api/forgot-password/send/    -> email pe OTP bhejo
#   2) /api/forgot-password/verify/  -> OTP check karo
#   3) /api/forgot-password/reset/   -> naya password set karo
# Saara pending state session ('password_reset') me rehta hai —
# bilkul registration OTP flow jaisa.
# ─────────────────────────────────────────
RESET_RESEND_COOLDOWN = 30   # seconds — resend ke beech ka gap


def _send_password_reset_otp(email, otp_code, username):
    """Send the 6-digit password-reset OTP (plain-text + branded HTML)."""
    subject = "Your Kasauti International password reset code"
    text_body = (
        f"Hi {username},\n\n"
        f"Your OTP to reset your Kasauti International password is: {otp_code}\n\n"
        f"This code is valid for {OTP_VALIDITY_MINUTES} minutes. "
        "Do not share it with anyone.\n\n"
        "If you did not request a password reset, please ignore this email — your password will remain unchanged.\n\n"
        "Regards,\nTeam Kasauti International"
    )
    html_body = f"""
<div style="margin:0;padding:0;background:#faf9f6;font-family:'Poppins',Arial,sans-serif;">
  <div style="max-width:520px;margin:0 auto;padding:32px 20px;">
    <div style="height:6px;border-radius:6px;overflow:hidden;display:flex;margin-bottom:24px;">
      <span style="flex:1;background:#06b6d4;">&nbsp;</span>
      <span style="flex:1;background:#e0529c;">&nbsp;</span>
      <span style="flex:1;background:#eab308;">&nbsp;</span>
      <span style="flex:1;background:#7c3aed;">&nbsp;</span>
    </div>
    <div style="background:#ffffff;border:1px solid rgba(201,151,63,0.18);border-radius:18px;padding:32px 28px;box-shadow:0 20px 60px rgba(15,23,42,0.08);">
      <h1 style="margin:0 0 4px;font-size:20px;color:#0f172a;font-weight:700;">Kasauti International</h1>
      <p style="margin:0 0 24px;font-size:13px;color:#94a3b8;">Password Reset</p>
      <p style="margin:0 0 8px;font-size:15px;color:#0f172a;">Hi <b>{username}</b>,</p>
      <p style="margin:0 0 24px;font-size:14px;color:#475569;line-height:1.6;">
        We received a request to reset your account password. Use the verification code below to continue:
      </p>
      <div style="text-align:center;margin:0 0 24px;">
        <div style="display:inline-block;background:linear-gradient(135deg,#c9973f,#f5d08a);color:#ffffff;font-size:34px;font-weight:700;letter-spacing:10px;padding:16px 26px 16px 36px;border-radius:14px;">
          {otp_code}
        </div>
      </div>
      <p style="margin:0 0 6px;font-size:13px;color:#94a3b8;text-align:center;">
        This code is valid for {OTP_VALIDITY_MINUTES} minutes.
      </p>
      <p style="margin:0;font-size:15px;color:#000000;text-align:center;">
        If you did not request a password reset, please ignore this email — your password will remain unchanged.
      </p>
    </div>
    <p style="text-align:center;margin:20px 0 0;font-size:11px;color:#3d077b;">
      © Kasauti International LLP • Noida, India
    </p>
  </div>
</div>
"""
    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_body,
        fail_silently=False,
    )


def _send_password_changed_email(email, username):
    """Confirmation mail after a successful password reset (non-blocking)."""
    try:
        send_mail(
            subject="Your Kasauti International password was changed",
            message=(
                f"Hi {username},\n\n"
                "This is a confirmation that the password for your Kasauti International "
                "account was changed successfully just now.\n\n"
                "If you did not make this change, please contact us immediately.\n\n"
                "Regards,\nTeam Kasauti International"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    except Exception:
        pass


def _reset_session(request):
    return request.session.get('password_reset')


@require_POST
def forgot_password_send(request):
    """Step 1 — email lo, account dhundo, OTP bhejo. (Resend bhi yahi handle karta hai.)"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid data.'}, status=400)

    email = (data.get('email') or '').strip().lower()
    if not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return JsonResponse({'ok': False, 'error': 'Please enter a valid email address.'}, status=400)

    user = User.objects.filter(email__iexact=email).order_by('-id').first()
    if user is None:
        return JsonResponse(
            {'ok': False, 'error': 'No registered account found with this email address.'},
            status=404,
        )

    # Resend cooldown (same email par baar-baar spam na ho)
    pr = _reset_session(request)
    if pr and pr.get('email') == email and pr.get('last_sent'):
        try:
            last_sent = datetime.fromisoformat(pr['last_sent'])
            elapsed = (timezone.now() - last_sent).total_seconds()
            if elapsed < RESET_RESEND_COOLDOWN:
                wait = int(RESET_RESEND_COOLDOWN - elapsed)
                return JsonResponse(
                    {'ok': False, 'error': f'Please wait — {wait}s before requesting another OTP.'},
                    status=429,
                )
        except ValueError:
            pass

    otp_code = _generate_otp()
    request.session['password_reset'] = {
        'user_id': user.pk,
        'email': email,
        'otp': otp_code,
        'expires_at': (timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)).isoformat(),
        'last_sent': timezone.now().isoformat(),
        'attempts': 0,
        'verified': False,
    }
    request.session.modified = True

    try:
        _send_password_reset_otp(email, otp_code, user.username)
    except Exception:
        request.session.pop('password_reset', None)
        return JsonResponse(
            {'ok': False, 'error': 'There was an issue sending the OTP email. Please try again later.'},
            status=500,
        )

    return JsonResponse({
        'ok': True,
        'email_masked': _mask_email(email),
        'cooldown': RESET_RESEND_COOLDOWN,
    })


@require_POST
def forgot_password_verify(request):
    """Step 2 — 6-digit OTP verify karo."""
    pr = _reset_session(request)
    if not pr:
        return JsonResponse(
            {'ok': False, 'error': 'Session expired. Please restart the process.', 'restart': True},
            status=400,
        )

    # Expiry guard
    try:
        expires_at = datetime.fromisoformat(pr['expires_at'])
    except (KeyError, ValueError):
        expires_at = timezone.now()
    if timezone.now() > expires_at:
        request.session.pop('password_reset', None)
        return JsonResponse(
            {'ok': False, 'error': 'OTP has expired. Please request another OTP.', 'restart': True},
            status=400,
        )

    if pr.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
        request.session.pop('password_reset', None)
        return JsonResponse(
            {'ok': False, 'error': 'Too many failed attempts. Please restart the process.', 'restart': True},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid data.'}, status=400)

    entered = (data.get('otp') or '').strip()
    if entered and entered == pr.get('otp'):
        pr['verified'] = True
        pr['otp'] = ''          # OTP dobara use na ho sake
        request.session['password_reset'] = pr
        request.session.modified = True
        return JsonResponse({'ok': True})

    pr['attempts'] = pr.get('attempts', 0) + 1
    request.session['password_reset'] = pr
    request.session.modified = True
    remaining = max(0, OTP_MAX_ATTEMPTS - pr['attempts'])
    return JsonResponse(
        {'ok': False, 'error': f'Galat OTP. {remaining} attempt bache hain.'},
        status=400,
    )


@require_POST
def forgot_password_reset(request):
    """Step 3 — OTP verified hone ke baad naya password set karo."""
    pr = _reset_session(request)
    if not pr or not pr.get('verified'):
        return JsonResponse(
            {'ok': False, 'error': 'Session expired. Please restart the process.', 'restart': True},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid data.'}, status=400)

    p1 = data.get('password1') or ''
    p2 = data.get('password2') or ''

    if not p1 or not p2:
        return JsonResponse({'ok': False, 'error': 'Please fill in both password fields.'}, status=400)
    if p1 != p2:
        return JsonResponse({'ok': False, 'error': 'The two password fields do not match.'}, status=400)

    user = User.objects.filter(pk=pr.get('user_id')).first()
    if user is None:
        request.session.pop('password_reset', None)
        return JsonResponse(
            {'ok': False, 'error': 'Account not found. Please restart the process.', 'restart': True},
            status=400,
        )

    # Django ke standard password validators (min length, common password, etc.)
    try:
        validate_password(p1, user=user)
    except DjangoValidationError as e:
        return JsonResponse({'ok': False, 'error': ' '.join(e.messages)}, status=400)

    user.set_password(p1)
    user.save(update_fields=['password'])

    request.session.pop('password_reset', None)
    request.session.modified = True
    _send_password_changed_email(user.email, user.username)

    return JsonResponse({'ok': True, 'username': user.username})


def otp(request):
    """
    Email-OTP verification for NEW registrations.

    Pending signup data + OTP live in the session ('pending_registration')
    until the correct 6-digit code is entered — only THEN is the User created.
    """
    pending = request.session.get('pending_registration')

    # No pending signup → back to login/register
    if not pending:
        messages.info(request, "Please fill out the registration form first.")
        return redirect('login')

    email_masked = _mask_email(pending.get('email', ''))

    # Expiry guard
    try:
        expires_at = datetime.fromisoformat(pending['expires_at'])
    except (KeyError, ValueError):
        expires_at = timezone.now()
    if timezone.now() > expires_at:
        request.session.pop('pending_registration', None)
        messages.error(request, "OTP has expired. Please request another OTP.")
        return redirect('login')

    if request.method == 'POST':
        sub_action = request.POST.get('action', 'verify')

        # ---- Resend OTP ----
        if sub_action == 'resend':
            new_otp = _generate_otp()
            pending['otp'] = new_otp
            pending['expires_at'] = (
                timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
            ).isoformat()
            pending['attempts'] = 0
            request.session['pending_registration'] = pending
            request.session.modified = True
            try:
                _send_registration_otp(pending['email'], new_otp, pending['username'])
                messages.success(request, "A new OTP has been sent to your email.")
            except Exception:
                messages.error(request, "Failed to resend OTP. Please try again later.")
            return redirect('otp')

        # ---- Verify OTP ----
        if pending.get('attempts', 0) >= OTP_MAX_ATTEMPTS:
            request.session.pop('pending_registration', None)
            messages.error(request, "Too many failed attempts. Please restart the process.")
            return redirect('login')

        entered = (request.POST.get('uotp') or '').strip()

        if entered and entered == pending.get('otp'):
            # ✅ Correct → create the account NOW
            try:
                user = User.objects.create_user(
                    username=pending['username'],
                    email=pending['email'],
                    password=pending['password'],
                )
            except Exception:
                request.session.pop('pending_registration', None)
                messages.error(request, "That username is already taken. Please try a different username.")
                return redirect('login')

            request.session.pop('pending_registration', None)
            _send_welcome_email(user.email, user.username)
            login(request, user)
            # Themed success screen (user already logged in)
            return render(request, 'otp.html', {
                'success': True,
                'reg_username': user.username,
            })

        # ❌ Wrong code
        pending['attempts'] = pending.get('attempts', 0) + 1
        request.session['pending_registration'] = pending
        request.session.modified = True
        remaining = max(0, OTP_MAX_ATTEMPTS - pending['attempts'])
        return render(request, 'otp.html', {
            'msg': f"Invalid OTP. {remaining} attempts remaining.",
            'email_masked': email_masked,
        })

    # GET
    return render(request, 'otp.html', {'email_masked': email_masked})

# ─────────────────────────────────────────
# Products: 3-category landing → category list → product detail
# ─────────────────────────────────────────

# Friendly URL slug  →  Product.category value in the DB
CATEGORY_MAP = {
    'ink': 'dtf_ink',
    'rolls': 'dtf_rolls',
    'powder': 'dtf_powder',
    'sublimation': 'sublimation_paper',
}

# Display info for each of the 4 category boxes (CMYK theme accents)
CATEGORY_META = {
    'ink': {
        'name': 'DTF Ink',
        'sub': 'CMYK + White',
        'desc': 'Cyan, Magenta, Yellow, Black & White — vibrant, fast-drying DTF inks.',
        'icon': 'fa-droplet',
        'accent': '#06b6d4',
        'img': 'image/ink.jpg',
    },
    'rolls': {
        'name': 'DTF Rolls',
        'sub': 'Film Rolls',
        'desc': 'Smooth-feeding DTF film rolls in every width for clean, consistent transfers.',
        'icon': 'fa-wind',
        'accent': '#e0529c',
        'img': 'image/roll.jpg',
    },
    'powder': {
        'name': 'DTF Powder',
        'sub': 'Hot-Melt Adhesive',
        'desc': 'Fine hot-melt adhesive powder for strong wash-durable bonding.',
        'icon': 'fa-gem',
        'accent': '#eab308',
        'img': 'image/powder.jpg',
    },
    'sublimation': {
        'name': 'Sublimation Paper',
        'sub': 'High-Release',
        'desc': 'High-release sublimation transfer paper for vivid, durable prints on polyester & coated blanks.',
        'icon': 'fa-file-lines',
        'accent': '#7c3aed',
        'img': 'image/s_roll.png',
    },
}

# Order the boxes appear on the landing page: Ink, Rolls, Powder, Sublimation Paper
CATEGORY_ORDER = ['ink', 'rolls', 'powder', 'sublimation']

# Reverse map: DB category value → friendly URL slug (for cross-category links)
SLUG_BY_DB = {db: slug for slug, db in CATEGORY_MAP.items()}

# Categories that are split into quality sub-types (Ink is NOT split)
HAS_SUBCATEGORIES = {'rolls', 'powder', 'sublimation'}

# The order the 2 sub-boxes appear for each split category
SUBCATEGORY_ORDER = {
    'rolls': ['single_matte', 'double_matte'],
    'powder': ['standard', 'premium'],
    'sublimation': ['korean_virgin', 'virgin'],
}

# Where blank-subcategory products land (so existing items never break)
DEFAULT_SUB = {'rolls': 'single_matte', 'powder': 'standard', 'sublimation': 'korean_virgin'}

# Display info for each sub-box
SUBCATEGORY_META = {
    'rolls': {
        'single_matte': {
            'name': 'Single Matte', 'sub': 'Single-side matte',
            'desc': 'Single-side matte DTF film — smooth feeding and clean, consistent transfers.',
            'icon': 'fa-wind', 'accent': '#e0529c', 'img': 'image/roll.jpg',
        },
        'double_matte': {
            'name': 'Double Matte', 'sub': 'Double-side matte',
            'desc': 'Double-side matte DTF film for extra grip and even powder pickup on both faces.',
            'icon': 'fa-layer-group', 'accent': '#7c3aed', 'img': 'image/roll.jpg',
        },
    },
    'powder': {
        'standard': {
            'name': 'Standard Powder', 'sub': 'Everyday grade',
            'desc': 'Reliable hot-melt adhesive powder for everyday DTF production at a great value.',
            'icon': 'fa-gem', 'accent': '#eab308', 'img': 'image/25KG_POWDER.png',
        },
        'premium': {
            'name': 'Premium Powder', 'sub': 'Pro grade',
            'desc': 'Finer, stronger-bonding powder for premium wash-durability and a soft hand-feel.',
            'icon': 'fa-crown', 'accent': '#c9973f', 'img': 'image/25KG_POWDER.png',
        },
    },
    'sublimation': {
        'korean_virgin': {
            'name': 'Korean Virgin Paper', 'sub': 'Premium import',
            'desc': 'Premium Korean virgin sublimation paper — fast drying with crisp, high-ink-release transfers.',
            'icon': 'fa-star', 'accent': '#7c3aed', 'img': 'image/s_roll.png',
        },
        'virgin': {
            'name': 'Virgin Paper', 'sub': 'Value grade',
            'desc': 'Dependable virgin sublimation paper for vivid everyday transfers at a great value.',
            'icon': 'fa-file-lines', 'accent': '#06b6d4', 'img': 'image/s_roll.png',
        },
    },
}


def _sub_filter(qs, category, sub):
    """Filter a queryset to one sub-type. Blank-subcategory products fall under
    the category's DEFAULT_SUB so nothing ever disappears."""
    if sub == DEFAULT_SUB.get(category):
        return qs.filter(Q(subcategory=sub) | Q(subcategory=''))
    return qs.filter(subcategory=sub)


def _detail_url(p):
    """Build the correct detail URL for a product, honouring sub-categories."""
    slug = SLUG_BY_DB.get(p.category)
    if not slug:
        return None
    if slug in HAS_SUBCATEGORIES:
        sub = p.subcategory or DEFAULT_SUB[slug]
        return reverse('product_detail_sub', args=[slug, sub, p.product_id])
    return reverse('product_level2', args=[slug, p.product_id])


def product(request):
    """Products landing — shows 4 category boxes (Ink, Rolls, Powder, Sublimation Paper)."""
    categories = []
    for slug in CATEGORY_ORDER:
        meta = CATEGORY_META[slug]
        qs = Product.objects.filter(category=CATEGORY_MAP[slug], is_available=True)
        first = qs.first()
        categories.append({
            'slug': slug,
            'name': meta['name'],
            'sub': meta['sub'],
            'desc': meta['desc'],
            'icon': meta['icon'],
            'accent': meta['accent'],
            'count': qs.count(),
            # Use a real product image if one exists, else the themed static fallback
            'img': (first.image.url if (first and first.image) else None),
            'fallback_img': meta['img'],
        })

    return render(request, 'product.html', {
        'categories': categories,
        'active_slug': 'all',
        'user_logged_in': request.user.is_authenticated,
        'login_url': '/login/?next=/products/',
    })


def product_category(request, category):
    """Level-1 listing.
    Ink → shows its variants directly.
    Rolls / Powder → shows 2 quality sub-boxes (variants live one level deeper)."""
    db_category = CATEGORY_MAP.get(category)
    if not db_category:
        raise Http404("Unknown category")

    meta = CATEGORY_META[category]
    base_ctx = {
        'active_slug': category,
        'user_logged_in': request.user.is_authenticated,
        'login_url': f'/login/?next=/products/{category}/',
    }

    # Split categories → render the 2 sub-boxes
    if category in HAS_SUBCATEGORIES:
        base = Product.objects.filter(category=db_category, is_available=True)
        subs = []
        for s in SUBCATEGORY_ORDER[category]:
            m = SUBCATEGORY_META[category][s]
            qs = _sub_filter(base, category, s)
            subs.append({
                'slug': s, 'cat': category,
                'name': m['name'], 'sub': m['sub'], 'desc': m['desc'],
                'icon': m['icon'], 'accent': m['accent'], 'fallback_img': m['img'],
                'count': qs.count(),
            })
        return render(request, 'product_subboxes.html', {
            'meta': meta,
            'subs': subs,
            'crumbs': [{'label': 'Products', 'url': reverse('product')},
                       {'label': meta['name']}],
            **base_ctx,
        })

    # Ink (non-split) → variant listing
    products = list(Product.objects.filter(category=db_category, is_available=True))
    for p in products:
        p.detail_url = _detail_url(p)
    return render(request, 'product_category.html', {
        'products': products,
        'meta': meta,
        'heading': meta['name'],
        'subheading': meta['sub'],
        'crumbs': [{'label': 'Products', 'url': reverse('product')},
                   {'label': meta['name']}],
        **base_ctx,
    })


def product_subcategory(request, category, sub):
    """Level-2 listing for a split category — variants of one sub-type
    (e.g. all DTF Rolls, or all Premium Powder)."""
    db_category = CATEGORY_MAP.get(category)
    if not db_category or category not in HAS_SUBCATEGORIES:
        raise Http404("Unknown category")
    if sub not in SUBCATEGORY_META[category]:
        raise Http404("Unknown sub-category")

    meta = CATEGORY_META[category]
    smeta = SUBCATEGORY_META[category][sub]
    products = list(_sub_filter(
        Product.objects.filter(category=db_category, is_available=True), category, sub
    ))
    for p in products:
        p.detail_url = _detail_url(p)

    return render(request, 'product_category.html', {
        'products': products,
        'meta': {**meta, 'accent': smeta['accent'], 'icon': smeta['icon']},
        'heading': smeta['name'],
        'subheading': smeta['sub'],
        'crumbs': [
            {'label': 'Products', 'url': reverse('product')},
            {'label': meta['name'], 'url': reverse('product_category', args=[category])},
            {'label': smeta['name']},
        ],
        'active_slug': category,
        'user_logged_in': request.user.is_authenticated,
        'login_url': f'/login/?next=/products/{category}/{sub}/',
    })


def product_level2(request, category, node):
    """2nd URL segment dispatcher.
    Split categories (Rolls/Powder): `node` is a sub-type slug → sub listing.
    Ink: `node` is a product_id → the product detail page."""
    if category in HAS_SUBCATEGORIES:
        return product_subcategory(request, category, node)
    return _render_detail(request, category, node, sub=None)


def product_detail_sub(request, category, sub, product_id):
    """Detail page for a product inside a split category (3-segment URL)."""
    return _render_detail(request, category, product_id, sub=sub)


def _render_detail(request, category, product_id, sub=None):
    """Shared product-detail renderer for both Ink (2-seg URL) and
    Rolls/Powder (3-seg URL with a sub-type)."""
    db_category = CATEGORY_MAP.get(category)
    if not db_category:
        raise Http404("Unknown category")

    product_obj = get_object_or_404(
        Product, product_id=product_id, category=db_category, is_available=True
    )

    meta = CATEGORY_META[category]

    # Breadcrumbs (and accent) differ for split vs non-split categories
    crumbs = [{'label': 'Products', 'url': reverse('product')}]
    if category in HAS_SUBCATEGORIES:
        eff_sub = sub or product_obj.subcategory or DEFAULT_SUB[category]
        smeta = SUBCATEGORY_META[category].get(eff_sub, {})
        crumbs.append({'label': meta['name'], 'url': reverse('product_category', args=[category])})
        if smeta:
            crumbs.append({'label': smeta['name'],
                           'url': reverse('product_level2', args=[category, eff_sub])})
            meta = {**meta, 'accent': smeta['accent'], 'icon': smeta.get('icon', meta['icon'])}
    else:
        crumbs.append({'label': meta['name'], 'url': reverse('product_category', args=[category])})
    crumbs.append({'label': product_obj.title})

    # Photo gallery: main image first (top), then extra gallery photos (slide-able)
    gallery_images = []
    if product_obj.image:
        gallery_images.append({'url': product_obj.image.url, 'alt': product_obj.title})
    for gi in product_obj.gallery.all():
        if gi.image:
            gallery_images.append({'url': gi.image.url, 'alt': gi.alt_text or product_obj.title})

    # Suggestions: same-category first, then top up with other categories (cross-sell)
    suggestions = list(
        Product.objects.filter(category=db_category, is_available=True).exclude(pk=product_obj.pk)
    )
    if len(suggestions) < 8:
        extra = (
            Product.objects
            .filter(is_available=True, category__in=CATEGORY_MAP.values())
            .exclude(category=db_category)
            .exclude(pk=product_obj.pk)
        )
        suggestions += list(extra)

    related = []
    for p in suggestions[:8]:
        slug = SLUG_BY_DB.get(p.category)
        if not slug:
            continue
        related.append({'p': p, 'url': _detail_url(p), 'accent': CATEGORY_META[slug]['accent']})

    # Sizes with their own pricing (shown in inches). The price row defaults to
    # the first size and updates as the customer taps a size.
    size_rows = []
    for ps in product_obj.sizes.all():
        sell = ps.sell_price
        mrp = ps.mrp_price
        size_rows.append({
            'label': ps.label,
            'sell': sell,
            'mrp': mrp if (mrp and sell is not None and mrp > sell) else None,
            'off': ps.discount_percent,
        })

    if size_rows:
        price_display = dict(size_rows[0])
    else:
        base_mrp = (product_obj.original_price
                    if (product_obj.original_price and product_obj.original_price > product_obj.price)
                    else None)
        price_display = {
            'sell': product_obj.price,
            'mrp': base_mrp,
            'off': product_obj.discount_percent if base_mrp else 0,
        }

    return render(request, 'product_detail.html', {
        'product': product_obj,
        'meta': meta,
        'crumbs': crumbs,
        'gallery_images': gallery_images,
        'related': related,
        'sizes': size_rows,
        'price_display': price_display,
        'active_slug': category,
        'user_logged_in': request.user.is_authenticated,
        'login_url': f'/login/?next={request.path}',
    })


@require_POST
def notify_request(request):
    """Create a 'notify me when back in stock' request — appears in the admin panel."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    try:
        p = Product.objects.get(product_id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    _, created = StockNotification.objects.get_or_create(
        product=p, user=request.user, status='new',
        defaults={
            'name': (request.user.get_full_name() or request.user.username),
            'email': request.user.email,
        },
    )
    return JsonResponse({'success': True, 'already': not created})


@require_POST
def catalog_request(request):
    """Save a WhatsApp number from the home savings calculator so the customer
    can be sent product details / catalogs. Appears in the admin panel."""
    number = (request.POST.get('whatsapp_number') or '').strip()
    note = (request.POST.get('note') or '').strip()[:200]

    # Basic validation: keep only digits to count length (allow +, spaces, dashes in input)
    digits = re.sub(r'\D', '', number)
    if len(digits) < 10 or len(digits) > 15:
        return JsonResponse(
            {'ok': False, 'error': 'Please enter a valid WhatsApp number (10–15 digits).'},
            status=400,
        )

    CatalogRequest.objects.create(whatsapp_number=number, note=note)
    return JsonResponse(
        {'ok': True, 'message': 'Thanks! We will send the details to your WhatsApp shortly.'}
    )


def contact(request):
    """Contact page — saves inquiry to DB."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your inquiry has been submitted. We'll contact you within 24 hours.")
            return redirect('contact')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


# ─────────────────────────────────────────
# Auth
# ─────────────────────────────────────────

@ensure_csrf_cookie  # FIX 1: Guarantees CSRF cookie is set — prevents 403 on first POST
def login_view(request):
    """Login & Register combined page."""
    if request.user.is_authenticated:
        return redirect('profile')

    login_form = LoginForm()
    register_form = RegisterForm()
    active_panel = 'login'

    if request.method == 'POST':
        action = request.POST.get('action', 'login')

        if action == 'login':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                username = login_form.cleaned_data['username'].strip()
                password = login_form.cleaned_data['password']
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    next_url = request.GET.get('next', '/profile/')
                    return redirect(next_url)
                else:
                    messages.error(request, "Invalid username or password.")
            active_panel = 'login'

        elif action == 'register':
            register_form = RegisterForm(request.POST)
            if register_form.is_valid():
                # Account abhi create NAHI karte — pehle email OTP verify hoga.
                otp_code = _generate_otp()
                request.session['pending_registration'] = {
                    'username': register_form.cleaned_data['username'],
                    'email':    register_form.cleaned_data['email'],
                    'password': register_form.cleaned_data['password1'],
                    'otp':      otp_code,
                    'expires_at': (
                        timezone.now() + timedelta(minutes=OTP_VALIDITY_MINUTES)
                    ).isoformat(),
                    'attempts': 0,
                }
                request.session.modified = True
                try:
                    _send_registration_otp(
                        register_form.cleaned_data['email'],
                        otp_code,
                        register_form.cleaned_data['username'],
                    )
                    return redirect('otp')
                except Exception:
                    request.session.pop('pending_registration', None)
                    messages.error(
                        request,
                        "Failed to send OTP email. Please check your email address "
                        "or try again later."
                    )
                    active_panel = 'register'
            else:
                # Surface all field errors as messages
                for field, errs in register_form.errors.items():
                    for err in errs:
                        if field != '__all__':
                            messages.error(request, f"{err}")
                        else:
                            messages.error(request, err)
                active_panel = 'register'

    return render(request, 'login.html', {
        'login_form': login_form,
        'register_form': register_form,
        'active_panel': active_panel,
    })


def logout_view(request):
    """
    Logout WITH confirmation.

    Normal flow: base.html me included modal (includes/logout_modal.html)
    click intercept karta hai aur POST bhejta hai — tabhi logout hota hai.
    GET  -> fallback confirmation page (JS off ho to bhi direct logout nahi).
    POST -> actual logout.
    """
    if not request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out.")
        return redirect('home')

    return render(request, 'logout_confirm.html')


# ─────────────────────────────────────────
# Profile — FIX 3
# ─────────────────────────────────────────

@login_required
def profile(request):
    """User profile with order history. Logout button is here, NOT in navbar."""
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items').order_by('-created_at')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileForm(instance=user)

    return render(request, 'profile.html', {
        'form': form,
        'orders': orders,
    })


# ─────────────────────────────────────────
# Cart API — FIX 5 & 6: login required
# ─────────────────────────────────────────

# Cart lines are keyed by product + size, so the same product can sit in the
# cart in two different sizes as two separate lines. Size-less products keep a
# plain product_id key (this also keeps any older carts working unchanged).
CART_SEP = '::'


def _cart_key(product_id, size=''):
    size = (size or '').strip()
    return f"{product_id}{CART_SEP}{size}" if size else product_id


def _parse_cart_key(key):
    """Split a cart key back into (product_id, size)."""
    if key and CART_SEP in key:
        pid, size = key.split(CART_SEP, 1)
        return pid, size
    return key, ''


def _effective_price(product, size_label):
    """Selling price for a product at a given size label: the size's own price
    if set, otherwise the product's base price. Computed server-side so the
    client can never set its own price."""
    if size_label:
        ps = product.sizes.filter(label=size_label).first()
        if ps is not None:
            return ps.sell_price
    return product.price


def _get_session_cart(request):
    if 'cart' not in request.session:
        request.session['cart'] = {}
    return request.session['cart']


def _build_cart_payload(request):
    """Single source of truth for the cart JSON the front-end renders.
    Every cart endpoint returns this exact shape so the drawer always has
    items + totals — this is what fixes the 'empty cart on +/-' bug."""
    cart = _get_session_cart(request)
    items = []
    subtotal = Decimal('0')
    for key, qty in cart.items():
        pid, size = _parse_cart_key(key)
        try:
            p = Product.objects.get(product_id=pid, is_available=True)
            price = _effective_price(p, size)
            line_total = price * qty
            items.append({
                'key': key,
                'product_id': pid,
                'size': size,
                'title': p.title,
                'price': float(price),
                'qty': qty,
                'line_total': float(line_total),
                'img': p.image.url if p.image else '',
            })
            subtotal += line_total
        except Product.DoesNotExist:
            pass
    gst = subtotal * Decimal('0.18')
    total = subtotal + gst
    return {
        'success': True,
        'items': items,
        'subtotal': float(subtotal),
        'gst': float(gst),
        'total': float(total),
        'total_items': sum(cart.values()),
    }


@require_POST
def cart_add(request):
    """Login required (Fix 5). Returns the full cart payload."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'redirect': '/login/?next=/products/'}, status=401)

    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        size = (data.get('size') or '').strip()
        qty = int(data.get('qty', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    if not product_id:
        return JsonResponse({'error': 'Missing product_id'}, status=400)

    key = _cart_key(product_id, size)
    cart = _get_session_cart(request)
    cart[key] = cart.get(key, 0) + qty
    request.session.modified = True
    _sync_cart_to_db(request.user, cart)

    return JsonResponse(_build_cart_payload(request))


@require_POST
def cart_remove(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)

    try:
        data = json.loads(request.body)
        key = data.get('key') or data.get('product_id')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    cart = _get_session_cart(request)
    cart.pop(key, None)
    request.session.modified = True
    _sync_cart_to_db(request.user, cart)

    return JsonResponse(_build_cart_payload(request))


@require_POST
def cart_update(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)

    try:
        data = json.loads(request.body)
        key = data.get('key') or data.get('product_id')
        qty = int(data.get('qty', 1))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    cart = _get_session_cart(request)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = qty
    request.session.modified = True
    _sync_cart_to_db(request.user, cart)  # keep DB cart in sync on every change

    return JsonResponse(_build_cart_payload(request))


def cart_clear(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'redirect': '/login/'}, status=401)

    request.session['cart'] = {}
    request.session.modified = True
    CartItem.objects.filter(user=request.user).delete()
    return JsonResponse(_build_cart_payload(request))


def cart_detail(request):
    if not request.user.is_authenticated:
        return JsonResponse({'items': [], 'subtotal': 0, 'gst': 0, 'total': 0, 'total_items': 0})
    return JsonResponse(_build_cart_payload(request))


def _sync_cart_to_db(user, cart_dict):
    CartItem.objects.filter(user=user).delete()
    for key, qty in cart_dict.items():
        pid, size = _parse_cart_key(key)
        try:
            p = Product.objects.get(product_id=pid)
            CartItem.objects.create(user=user, product=p, quantity=qty, size=size)
        except Product.DoesNotExist:
            pass


# ─────────────────────────────────────────
# Checkout — FIX 2: login required
# ─────────────────────────────────────────

@login_required  # Django will redirect to /login/?next=/checkout/ automatically
def checkout(request):
    cart = _get_session_cart(request)
    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('product')

    cart_items = []
    subtotal = Decimal('0')
    for key, qty in cart.items():
        pid, size = _parse_cart_key(key)
        try:
            p = Product.objects.get(product_id=pid, is_available=True)
            price = _effective_price(p, size)
            line_total = price * qty
            cart_items.append({'product': p, 'qty': qty, 'size': size,
                               'price': price, 'line_total': line_total})
            subtotal += line_total
        except Product.DoesNotExist:
            pass

    if not cart_items:
        messages.warning(request, "Your cart is empty or products are unavailable.")
        return redirect('product')

    gst = subtotal * Decimal('0.18')
    total = subtotal + gst

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.total_amount = total
            order.gst_amount = gst
            order.user = request.user
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_title=item['product'].title,
                    size=item['size'],
                    unit_price=item['price'],
                    quantity=item['qty'],
                )

            request.session['cart'] = {}
            request.session.modified = True
            CartItem.objects.filter(user=request.user).delete()

            messages.success(request, f"Order #{order.id} placed! We'll contact you soon.")
            return redirect('order_success', order_id=order.id)
        else:
            messages.error(request, "Please fill all required fields correctly.")
    else:
        form = CheckoutForm(initial={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })

    return render(request, 'checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst': gst,
        'total': total,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_success.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'my_orders.html', {'orders': orders})

def home(request):
    context = {
        "reviews": CustomerReview.objects.filter(is_published=True),
        "reels": ReelVideo.objects.filter(is_published=True),
    }
    return render(request, "home.html", context)

# ─────────────────────────────────────────
# Custom 404 — brand-themed "misprint" page
# ─────────────────────────────────────────

def custom_404(request, exception=None):
    """
    Custom 404 page (templates/404.html).

    - DEBUG=False: handler404 ke through render hota hai.
    - DEBUG=True: project urls.py ka catch-all pattern yahan bhejta hai.

    Catch-all ki wajah se Django ka APPEND_SLASH redirect kaam nahi karta,
    isliye wahi behaviour yahan manually hai: agar '/about' jaisa URL bina
    slash ke aaye aur '/about/' valid ho, to wahan redirect kar do.
    """
    from django.urls import resolve, Resolver404

    path = request.path
    if not path.endswith('/'):
        try:
            match = resolve(path + '/')
            # Slash lagane par koi REAL view milta hai (khud 404 nahi) -> redirect
            if match.func is not custom_404:
                return redirect(path + '/')
        except Resolver404:
            pass

    return render(request, '404.html', status=404)


def preview_404(request):
    """DEBUG=True me bhi 404 page dekhne ke liye: /404-preview/"""
    return render(request, '404.html', status=404)


# ─────────────────────────────────────────
# Media serving WITH HTTP Range support (for video playback)
# Django's built-in static serve does NOT support range requests, which
# breaks <video> playback/seeking in Chrome. This view fixes that in dev.
# In production, a real web server (nginx/Apache) handles ranges natively.
# ─────────────────────────────────────────

def serve_media(request, path):
    """Serve a file from MEDIA_ROOT with HTTP Range support (206 responses)."""
    media_root = os.path.normpath(str(settings.MEDIA_ROOT))
    full_path = os.path.normpath(os.path.join(media_root, path))

    if not full_path.startswith(media_root):
        raise Http404("Not found")
    if not os.path.isfile(full_path):
        raise Http404("Not found")

    file_size = os.path.getsize(full_path)
    content_type, _ = mimetypes.guess_type(full_path)
    content_type = content_type or 'application/octet-stream'

    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

    if range_match:
        start = int(range_match.group(1))
        end_group = range_match.group(2)
        end = int(end_group) if end_group else file_size - 1
        max_chunk = 8 * 1024 * 1024  # 8 MB per chunk
        end = min(end, start + max_chunk - 1, file_size - 1)

        if start >= file_size or start > end:
            resp = HttpResponse(status=416)
            resp['Content-Range'] = f'bytes */{file_size}'
            return resp

        length = end - start + 1

        def chunk_iter():
            with open(full_path, 'rb') as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    block = f.read(min(8192, remaining))
                    if not block:
                        break
                    remaining -= len(block)
                    yield block

        resp = StreamingHttpResponse(chunk_iter(), status=206, content_type=content_type)
        resp['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        resp['Accept-Ranges'] = 'bytes'
        resp['Content-Length'] = str(length)
        return resp

    resp = FileResponse(open(full_path, 'rb'), content_type=content_type)
    resp['Accept-Ranges'] = 'bytes'
    resp['Content-Length'] = str(file_size)
    return resp
