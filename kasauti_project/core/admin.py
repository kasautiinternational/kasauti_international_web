from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Product, ProductImage, ProductSize, ContactInquiry, CartItem, Order, OrderItem,
    CustomerReview, ReelVideo, DistributorInquiry, StockNotification, CatalogRequest,
)


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
class ContactInquiryAdmin(admin.ModelAdmin):
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
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'phone', 'display_total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'phone']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'total_amount', 'gst_amount', 'user']
    inlines = [OrderItemInline]
    ordering = ['-created_at']

    def display_total(self, obj):
        if obj.total_amount is not None:
            return f"₹{obj.total_amount:,.2f}"
        return "—"
    display_total.short_description = 'Total'
    display_total.admin_order_field = 'total_amount'


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
class DistributorInquiryAdmin(admin.ModelAdmin):
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
class StockNotificationAdmin(admin.ModelAdmin):
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
class CatalogRequestAdmin(admin.ModelAdmin):
    list_display = ['whatsapp_number', 'note', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['whatsapp_number', 'note']
    list_editable = ['status']
    readonly_fields = ['whatsapp_number', 'note', 'created_at']
    ordering = ['-created_at']
