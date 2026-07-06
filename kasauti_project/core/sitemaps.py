from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Product


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
        return list(
            Product.objects.values_list('category', flat=True).distinct()
        )

    def location(self, item):
        return reverse('product_category', args=[item])


class ProductSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Product.objects.exclude(
            subcategory__isnull=True
        ).exclude(subcategory='')

    def location(self, obj):
        return reverse(
            'product_detail_sub',
            args=[obj.category, obj.subcategory, obj.id]
        )