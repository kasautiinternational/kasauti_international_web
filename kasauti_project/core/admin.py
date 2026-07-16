from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import (
    Product, ProductImage, ProductSize, ContactInquiry, CartItem, Order, OrderItem,
    CustomerReview, ReelVideo, DistributorInquiry, StockNotification, CatalogRequest,
    AdminSeen,
)


# ─────────────────────────────────────────
# NEW: Admin sidebar notification badges
# Naya order / inquiry / notify-me / catalog request / user registration
# aate hi admin sidebar me us model ke aage red count badge dikhega.
# List open karte hi sab 'seen' mark ho jata hai aur badge clear.
# ─────────────────────────────────────────

BADGE_MODELS = [
    Order,
    ContactInquiry,
    DistributorInquiry,
    StockNotification,
    CatalogRequest,
]


class NewBadgeAdminMixin:
    """Jaise hi admin is model ki list kholta hai, saare unseen
    records 'seen' mark ho jate hain (badge clear)."""

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        def mark_seen(resp):
            self.model.objects.filter(is_seen=False).update(is_seen=True)
            return resp

        # Page render hone ke BAAD seen mark karo, taki list me
        # 'new' wale rows pehli baar highlight/filter ho saken.
        if hasattr(response, 'add_post_render_callback'):
            response.add_post_render_callback(mark_seen)
        else:
            self.model.objects.filter(is_seen=False).update(is_seen=True)
        return response


def _users_seen_until():
    """Kab tak ke users admin dekh chuka hai — tracker se timestamp lao."""
    tracker, _ = AdminSeen.objects.get_or_create(
        key='auth_user', defaults={'seen_until': timezone.now()}
    )
    return tracker


@staff_member_required
def admin_new_counts(request):
    """JSON endpoint — base_site.html ka JS isse counts uthata hai."""
    data = {}
    for model in BADGE_MODELS:
        count = model.objects.filter(is_seen=False).count()
        if count:
            url = "/admin/{}/{}/".format(model._meta.app_label, model._meta.model_name)
            data[url] = count

    # NEW: naye registered users ka badge (built-in User model me field
    # add nahi kar sakte, isliye date_joined + tracker se count karte hain)
    tracker = _users_seen_until()
    new_users = User.objects.filter(date_joined__gt=tracker.seen_until).count()
    if new_users:
        data['/admin/auth/user/'] = new_users

    return JsonResponse(data)


# ─────────────────────────────────────────
# NEW: Users list pe bhi badge — default UserAdmin ko replace karke
# ─────────────────────────────────────────

class BadgedUserAdmin(DjangoUserAdmin):
    """Django ka normal Users admin hi hai, plus:
    - Naye (unseen) users ke aage red NEW tag
    - 'Joined' column — kitna time pehle register hua
    - Newest users sabse upar
    - List kholte hi tracker update (sidebar badge clear)"""

    list_display = ['username', 'email', 'first_name', 'last_name',
                    'is_staff', 'new_tag', 'joined_ago', 'date_joined']
    ordering = ['-date_joined']

    def changelist_view(self, request, extra_context=None):
        # NEW tags render hone tak purana tracker chahiye, isliye pehle cache karo
        self._seen_until = _users_seen_until().seen_until
        response = super().changelist_view(request, extra_context)

        def mark_seen(resp):
            AdminSeen.objects.update_or_create(
                key='auth_user', defaults={'seen_until': timezone.now()}
            )
            return resp

        if hasattr(response, 'add_post_render_callback'):
            response.add_post_render_callback(mark_seen)
        else:
            AdminSeen.objects.update_or_create(
                key='auth_user', defaults={'seen_until': timezone.now()}
            )
        return response

    def new_tag(self, obj):
        """Red NEW pill — sirf un users pe jo last dekhe jane ke baad aaye."""
        seen = getattr(self, '_seen_until', None)
        if seen is None:
            seen = _users_seen_until().seen_until
        if obj.date_joined and obj.date_joined > seen:
            return format_html(
                '<span style="background:#e53935;color:#fff;font-size:10px;'
                'font-weight:700;padding:2px 8px;border-radius:10px;">NEW</span>'
            )
        return ''
    new_tag.short_description = ''

    def joined_ago(self, obj):
        """Kitna time pehle join kiya — e.g. '2 days ago', 'Just now'."""
        if not obj.date_joined:
            return '—'
        delta = timezone.now() - obj.date_joined
        secs = int(delta.total_seconds())
        if secs < 60:
            return 'Just now'
        mins = secs // 60
        if mins < 60:
            return f'{mins} min ago'
        hours = mins // 60
        if hours < 24:
            return f'{hours} hr ago' if hours == 1 else f'{hours} hrs ago'
        days = hours // 24
        if days < 30:
            return f'{days} day ago' if days == 1 else f'{days} days ago'
        months = days // 30
        if months < 12:
            return f'{months} month ago' if months == 1 else f'{months} months ago'
        years = days // 365
        return f'{years} year ago' if years == 1 else f'{years} years ago'
    joined_ago.short_description = 'Joined'
    joined_ago.admin_order_field = 'date_joined'
    
admin.site.unregister(User)
admin.site.register(User, BadgedUserAdmin)


class ProductImageInline(admin.TabularInline):
    """Add multiple gallery photos right inside the Product edit page."""
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'order']


class ProductSizeInline(admin.TabularInline):
    """Add the selectable sizes (shown in inches) right inside the Product
    edit page, each with its own price. Leave a size's price blank to use the
    product's base price. Leave the whole block empty for products with no size."""
    model = ProductSize
    extra = 3
    fields = ['label', 'price', 'original_price', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subcategory', 'price', 'original_price', 'stock', 'is_available', 'updated_at']
    list_filter = ['category', 'subcategory', 'is_available']
    search_fields = ['title', 'description', 'product_id']
    list_editable = ['subcategory', 'price', 'original_price', 'stock', 'is_available']
    ordering = ['category', 'title']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline, ProductSizeInline]

    fieldsets = (
        ('Product details', {
            'fields': ('product_id', 'title', 'description', 'category', 'subcategory', 'tag', 'image', 'accent_color'),
            'description': "For Rolls & Powder, pick a 'subcategory' (quality type). Leave it blank for Ink.",
        }),
        ('Pricing & stock', {
            'fields': ('original_price', 'price', 'stock', 'is_available'),
            'description': "Set 'original_price' (MRP) higher than 'price' to show a struck-through "
                           "MRP with the discounted selling price. Set 'stock' to 0 to mark a product "
                           "Out of Stock (shows an overlay + a 'Notify Me' button instead of Add/Buy).",
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ContactInquiry)
class ContactInquiryAdmin(NewBadgeAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'product', 'quantity', 'status', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['name', 'email', 'phone', 'message']
    list_editable = ['status']
    readonly_fields = ['submitted_at']
    ordering = ['-submitted_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # FIX 4: Only DB fields in readonly_fields. 'line_total' is a Python @property
    # and cannot be listed here — use a custom method instead.
    readonly_fields = ['product_title', 'size', 'unit_price', 'quantity', 'display_line_total']
    fields = ['product', 'product_title', 'size', 'unit_price', 'quantity', 'display_line_total']

    def display_line_total(self, obj):
        if obj and obj.pk and obj.unit_price is not None and obj.quantity is not None:
            total = obj.unit_price * obj.quantity
            return f"₹{total:,.2f}"
        return "—"
    display_line_total.short_description = 'Line Total'


@admin.register(Order)
class OrderAdmin(NewBadgeAdminMixin, admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone', 'display_total', 'status', 'created_at', 'invoice_button']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'phone']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'total_amount', 'gst_amount', 'user']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    change_form_template = 'admin/core/order/change_form.html'  # NEW: Download Invoice button

    def display_total(self, obj):
        if obj.total_amount is not None:
            return f"₹{obj.total_amount:,.2f}"
        return "—"
    display_total.short_description = 'Total'
    display_total.admin_order_field = 'total_amount'

    # ─── NEW: Invoice PDF download ───
    def invoice_button(self, obj):
        return format_html(
            '<a class="button" style="background:#c9973f;color:#0f172a;'
            'font-weight:bold;padding:4px 10px;border-radius:4px;" '
            'href="{}">Invoice</a>',
            f'{obj.id}/invoice/'
        )
    invoice_button.short_description = 'Invoice'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                '<int:order_id>/invoice/',
                self.admin_site.admin_view(self.download_invoice),
                name='core_order_invoice',
            ),
        ]
        return custom + urls

    def download_invoice(self, request, order_id):
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        from .invoice import build_invoice_pdf

        order = get_object_or_404(
            Order.objects.prefetch_related('items'), id=order_id
        )
        pdf_bytes = build_invoice_pdf(order)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="Invoice-KI-{order.id:05d}.pdf"'
        )
        return response


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'size', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__title']


# ─────────────────────────────────────────
# Home page content — Reviews & Reels
# ─────────────────────────────────────────

@admin.register(CustomerReview)
class CustomerReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'star_display', 'short_message', 'is_published', 'order', 'created_at']
    list_filter = ['is_published', 'rating', 'created_at']
    search_fields = ['name', 'role', 'message']
    list_editable = ['is_published', 'order']
    readonly_fields = ['created_at']
    ordering = ['order', '-created_at']

    fieldsets = (
        ('Review', {'fields': ('name', 'role', 'rating', 'message')}),
        ('Display settings', {'fields': ('is_published', 'order', 'created_at')}),
    )

    def star_display(self, obj):
        return '★' * int(obj.rating)
    star_display.short_description = 'Rating'

    def short_message(self, obj):
        return (obj.message[:60] + '…') if len(obj.message) > 60 else obj.message
    short_message.short_description = 'Message'


@admin.register(ReelVideo)
class ReelVideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'media_preview', 'media_kind', 'accent', 'is_published', 'order', 'created_at']
    list_filter = ['is_published', 'accent', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['accent', 'is_published', 'order']
    readonly_fields = ['created_at', 'media_preview']
    ordering = ['order', '-created_at']

    fieldsets = (
        ('Video', {
            'fields': ('title', 'subtitle', 'video_file', 'external_url', 'poster', 'media_preview'),
            'description': "Upload an mp4 file (recommended) OR paste a YouTube/Instagram link. "
                           "If both are given, the uploaded file is used.",
        }),
        ('Display settings', {'fields': ('accent', 'is_published', 'order', 'created_at')}),
    )

    def media_preview(self, obj):
        if obj.poster:
            return format_html('<img src="{}" style="height:90px;border-radius:8px;" />', obj.poster.url)
        if obj.video_file:
            return format_html(
                '<video src="{}" style="height:90px;border-radius:8px;" muted controls></video>',
                obj.video_file.url
            )
        if obj.external_url:
            return format_html('<span style="color:#0e7490;">🔗 {}</span>', obj.media_kind.title())
        return '—'
    media_preview.short_description = 'Preview'


# ─────────────────────────────────────────
# Distributor applications
# ─────────────────────────────────────────

@admin.register(DistributorInquiry)
class DistributorInquiryAdmin(NewBadgeAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'city', 'phone', 'business_type', 'status', 'submitted_at']
    list_filter = ['status', 'business_type', 'submitted_at']
    search_fields = ['name', 'city', 'phone']
    list_editable = ['status']
    readonly_fields = ['submitted_at']
    ordering = ['-submitted_at']

    fieldsets = (
        ('Applicant details', {'fields': ('name', 'city', 'phone', 'business_type')}),
        ('Follow-up', {'fields': ('status', 'notes', 'submitted_at')}),
    )

# ─────────────────────────────────────────
# Back-in-stock "Notify Me" requests
# ─────────────────────────────────────────

@admin.register(StockNotification)
class StockNotificationAdmin(NewBadgeAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'user', 'email', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'product']
    search_fields = ['product__title', 'user__username', 'email', 'name']
    list_editable = ['status']
    readonly_fields = ['product', 'user', 'name', 'email', 'created_at']
    ordering = ['-created_at']


# ─────────────────────────────────────────
# Catalog requests (WhatsApp numbers from the home savings calculator)
# ─────────────────────────────────────────

@admin.register(CatalogRequest)
class CatalogRequestAdmin(NewBadgeAdminMixin, admin.ModelAdmin):
    list_display = ['whatsapp_number', 'note', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['whatsapp_number', 'note']
    list_editable = ['status']
    readonly_fields = ['whatsapp_number', 'note', 'created_at']
    ordering = ['-created_at']