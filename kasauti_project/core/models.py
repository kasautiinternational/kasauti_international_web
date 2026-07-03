from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    """Products sold by KASAUTI INTERNATIONAL."""
    CATEGORY_CHOICES = [
        ('dtf_rolls', 'DTF Rolls'),
        ('dtf_ink', 'DTF Ink'),
        ('dtf_powder', 'DTF Powder'),
        ('sublimation_paper', 'Sublimation Paper'),
        ('project_special', 'Special Product'),
    ]

    # Quality sub-types — used by Rolls, Powder & Sublimation Paper (Ink stays blank)
    SUBCATEGORY_CHOICES = [
        ('', '— None (Ink / no sub-type) —'),
        ('single_matte', 'Rolls › Single Matte'),
        ('double_matte', 'Rolls › Double Matte'),
        ('standard', 'Powder › Standard'),
        ('premium', 'Powder › Premium'),
        ('korean_virgin', 'Sublimation Paper › Korean Virgin Paper'),
        ('virgin', 'Sublimation Paper › Virgin Paper'),
    ]

    product_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text="Optional MRP shown with a strike-through above the selling price. "
                  "Leave blank if there is no discount."
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(
        max_length=20, blank=True, default='', choices=SUBCATEGORY_CHOICES,
        help_text="Only for Rolls, Powder & Sublimation Paper — splits them into quality types. Leave blank for Ink."
    )
    tag = models.CharField(max_length=100)
    image = models.ImageField(
        upload_to='products/', blank=True, null=True,
        help_text="Main photo — shown first (top) on the product detail page."
    )
    accent_color = models.CharField(max_length=20, default='#06b6d4')
    is_available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']

    def __str__(self):
        return self.title

    @property
    def discount_percent(self):
        """Whole-number % off — used for the strike-through price badge."""
        if self.original_price and self.original_price > self.price:
            return int(round((self.original_price - self.price) / self.original_price * 100))
        return 0

    @property
    def in_stock(self):
        """True when there is stock to sell; False shows the 'Out of Stock' UI."""
        return self.stock > 0


class ProductImage(models.Model):
    """Extra gallery photos for a product. The main photo stays on Product.image
    and is always shown first; these are the additional slide-able photos."""
    product = models.ForeignKey(Product, related_name='gallery', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Photo for {self.product.title}"


class ProductSize(models.Model):
    """Selectable size options for a product (e.g. sublimation paper sheet sizes).
    Admin adds the sizes here and they appear as tappable buttons next to
    Add to Cart / Buy Now on the product detail page, shown in inches.
    Each size can have its own price; the price shown updates as the customer
    taps a size. Leave a size's price blank to use the product's base price.
    Leave the whole block empty for products that don't need a size (Ink, etc.)."""
    product = models.ForeignKey(Product, related_name='sizes', on_delete=models.CASCADE)
    label = models.CharField(
        max_length=50,
        help_text='Just the size value in inches — e.g. "13 x 19", "24" or "36". '
                  'The "(in inches)" label is shown automatically; no need to type it.'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Selling price (₹) for THIS size. Leave blank to use the product's base price."
    )
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Optional MRP (₹) for this size — shown struck-through above the price. "
                  "Leave blank if this size has no discount."
    )
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first.")

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        p = f" — ₹{self.price:,.0f}" if self.price is not None else ""
        return f"{self.label} in{p} — {self.product.title}"

    @property
    def sell_price(self):
        """This size's price if set, otherwise the product's base price."""
        return self.price if self.price is not None else self.product.price

    @property
    def mrp_price(self):
        """MRP to strike through: this size's MRP if it has its own price,
        otherwise the product's base MRP."""
        if self.price is not None:
            return self.original_price
        return self.product.original_price

    @property
    def discount_percent(self):
        sell, mrp = self.sell_price, self.mrp_price
        if mrp and sell is not None and mrp > sell:
            return int(round((mrp - sell) / mrp * 100))
        return 0


class StockNotification(models.Model):
    """A 'notify me when back in stock' request from a customer.
    These show up in the Django admin panel so you can follow up."""
    STATUS_CHOICES = [('new', 'New'), ('notified', 'Notified')]

    product = models.ForeignKey(Product, related_name='stock_notifications', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        who = self.user.username if self.user else (self.email or 'guest')
        return f"{self.product.title} — {who}"


class ContactInquiry(models.Model):
    """Stores all contact form submissions."""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    product = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Inquiry'
        verbose_name_plural = 'Contact Inquiries'

    def __str__(self):
        return f"{self.name} — {self.submitted_at.strftime('%d %b %Y')}"


class CartItem(models.Model):
    """Server-side cart item (tied to a logged-in user)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Selected size in inches (e.g. 13 x 19). Blank for products without sizes."
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Same product in two different sizes = two separate cart lines.
        unique_together = ('user', 'product', 'size')

    def __str__(self):
        s = f" [{self.size} in]" if self.size else ""
        return f"{self.user.username} — {self.product.title}{s} x{self.quantity}"

    @property
    def subtotal(self):
        price = self.product.price
        if self.size:
            ps = self.product.sizes.filter(label=self.size).first()
            if ps is not None:
                price = ps.sell_price
        return price * self.quantity


class Order(models.Model):
    """Order placed by a user (after checkout)."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.name} ({self.status})"


class OrderItem(models.Model):
    """Individual line items in an Order."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_title = models.CharField(max_length=200)  # snapshot at order time
    size = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Selected size in inches at order time. Blank if the product had no sizes."
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        s = f" [{self.size} in]" if self.size else ""
        return f"{self.product_title}{s} x{self.quantity}"

    @property
    def line_total(self):
        if self.unit_price is not None and self.quantity is not None:
            return self.unit_price * self.quantity
        return 0


class CustomerReview(models.Model):
    """Text feedback shown in the reviews carousel on the home page.
    Admin adds reviews here; only is_published=True reviews appear on the site."""
    name = models.CharField(max_length=120, help_text="Customer name, e.g. Ravi K.")
    role = models.CharField(
        max_length=120, blank=True,
        help_text="Business / role shown under the name, e.g. Print Studio"
    )
    rating = models.PositiveSmallIntegerField(
        default=5,
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')],
        help_text="Star rating (1-5)"
    )
    message = models.TextField(help_text="The review text. Hinglish is fine.")
    is_published = models.BooleanField(
        default=True,
        help_text="Untick to hide this review from the website without deleting it."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower number shows first. Same numbers fall back to newest first."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Customer Review'
        verbose_name_plural = 'Customer Reviews'

    def __str__(self):
        return f"{self.name} ({self.rating} star)"

    @property
    def stars(self):
        """Filled stars string for the template, e.g. '★★★★★'."""
        return '★' * int(self.rating)


class ReelVideo(models.Model):
    """Video reviews shown in the reels carousel on the home page.
    Admin can upload an mp4 file OR paste a YouTube/Instagram link.
    If both are given, the uploaded file is used. Only is_published=True reels show."""
    ACCENT_CHOICES = [
        ('cyan', 'Cyan'),
        ('magenta', 'Magenta'),
        ('yellow', 'Yellow'),
        ('violet', 'Violet'),
    ]

    title = models.CharField(max_length=120, help_text="Caption heading, e.g. Ink Lay Test")
    subtitle = models.CharField(
        max_length=160, blank=True,
        help_text="Small caption under the title, e.g. Vibrant CMYK+W output"
    )
    video_file = models.FileField(
        upload_to='reels/', blank=True, null=True,
        help_text="Upload an mp4 video (recommended). It auto-plays on the site."
    )
    external_url = models.URLField(
        blank=True,
        help_text="Optional: a YouTube or Instagram link (used only if no file is uploaded)."
    )
    poster = models.ImageField(
        upload_to='reel_posters/', blank=True, null=True,
        help_text="Optional thumbnail image (used for external links)."
    )
    accent = models.CharField(
        max_length=10, choices=ACCENT_CHOICES, default='cyan',
        help_text="Border/glow colour for the card (CMYK theme)."
    )
    is_published = models.BooleanField(
        default=True,
        help_text="Untick to hide this reel from the website without deleting it."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower number shows first. Same numbers fall back to newest first."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Reel Video'
        verbose_name_plural = 'Reel Videos'

    def __str__(self):
        return self.title

    def _youtube_id(self):
        url = (self.external_url or '').strip()
        if 'youtu' not in url:
            return ''
        if 'watch?v=' in url:
            return url.split('watch?v=')[-1].split('&')[0]
        if 'youtu.be/' in url:
            return url.split('youtu.be/')[-1].split('?')[0].split('&')[0]
        if '/shorts/' in url:
            return url.split('/shorts/')[-1].split('?')[0].split('&')[0]
        if '/embed/' in url:
            return url.split('/embed/')[-1].split('?')[0].split('&')[0]
        return ''

    @property
    def media_kind(self):
        """Returns 'file', 'youtube', 'instagram', or 'none' for the template."""
        if self.video_file:
            return 'file'
        url = (self.external_url or '').strip().lower()
        if 'youtu' in url:
            return 'youtube'
        if 'instagram.com' in url:
            return 'instagram'
        return 'none'

    @property
    def embed_url(self):
        """Embeddable URL for iframe playback (YouTube / Instagram)."""
        kind = self.media_kind
        if kind == 'youtube':
            yid = self._youtube_id()
            if yid:
                return f"https://www.youtube.com/embed/{yid}?autoplay=1&mute=1&loop=1&playlist={yid}&rel=0&playsinline=1"
        elif kind == 'instagram':
            base = (self.external_url or '').strip().split('?')[0].rstrip('/')
            return f"{base}/embed"
        return ''


class DistributorInquiry(models.Model):
    """Distributor application form submissions from the Distributor page.
    Admin can view, edit, and update the status of each application."""
    BUSINESS_TYPE_CHOICES = [
        ('print_shop', 'Print shop'),
        ('reseller', 'Reseller'),
        ('distributor', 'Distributor'),
        ('studio', 'Studio'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    name = models.CharField(max_length=150)
    city = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    business_type = models.CharField(max_length=30, choices=BUSINESS_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField(blank=True, help_text="Internal notes (not shown to the applicant).")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Distributor Inquiry'
        verbose_name_plural = 'Distributor Inquiries'

    def __str__(self):
        return f"{self.name} - {self.city} ({self.get_status_display()})"


class CatalogRequest(models.Model):
    """WhatsApp number submitted from the home-page savings calculator.
    The customer wants product details / catalogs sent to their WhatsApp.
    These show up in the Django admin so you can follow up and send details."""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('sent', 'Details Sent'),
    ]

    whatsapp_number = models.CharField(max_length=20, help_text="Customer's WhatsApp number.")
    note = models.CharField(
        max_length=200, blank=True,
        help_text="Optional: what the customer was looking at (e.g. Rolls savings)."
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Catalog Request (WhatsApp)'
        verbose_name_plural = 'Catalog Requests (WhatsApp)'

    def __str__(self):
        return f"{self.whatsapp_number} ({self.get_status_display()})"
