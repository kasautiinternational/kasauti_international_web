from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product
from .views import CATEGORY_MAP, CATEGORY_ORDER, _detail_url


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'home', 'about', 'product', 'contact', 'distributor',
            'services', 'privacy_policy', 'terms_condition',
            'refund_return', 'shipping_policy',
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        # Friendly slugs: ink, rolls, powder, sublimation
        return CATEGORY_ORDER

    def location(self, item):
        return reverse('product_category', args=[item])


class ProductSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Product.objects.filter(
            is_available=True, category__in=CATEGORY_MAP.values()
        )

    def location(self, obj):
        # Views ka wahi helper jo site pe links banata hai — 
        # ink (2-segment) aur baaki (3-segment) dono handle karta hai
        return _detail_url(obj)