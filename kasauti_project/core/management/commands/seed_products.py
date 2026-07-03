"""
Management command: python manage.py seed_products

Seeds the Product table with the same 4 products shown in product.js,
so the admin can manage them via Django Admin.

Run this once after initial migrations:
    python manage.py migrate
    python manage.py seed_products
    python manage.py createsuperuser
"""

from django.core.management.base import BaseCommand
from core.models import Product


SEED_PRODUCTS = [
    {
        'product_id': 'dtf_rolls_b',
        'title': 'DTF Roll 30cm',
        'description': 'Consistent roll quality with smooth feeding for machines.',
        'price': '1899.00',
        'category': 'dtf_rolls',
        'tag': 'DTF Rolls',
        'accent_color': '#06b6d4',
        'stock': 100,
    },
    {
        'product_id': 'dtf_ink_c',
        'title': 'DTF Ink (Set)',
        'description': 'Fast-drying ink with strong adhesion for long-lasting prints.',
        'price': '749.00',
        'category': 'dtf_ink',
        'tag': 'DTF Ink',
        'accent_color': '#ef4444',
        'stock': 200,
    },
    {
        'product_id': 'dtf_powder_d',
        'title': 'DTF Powder',
        'description': 'Fine powder for crisp results and strong transfer bonding.',
        'price': '399.00',
        'category': 'dtf_powder',
        'tag': 'DTF Powder',
        'accent_color': '#f59e0b',
        'stock': 300,
    },
    {
        'product_id': 'project_special_e',
        'title': 'Special Project Bundle',
        'description': 'A curated bundle for creators: print + roll + ink + powder.',
        'price': '4799.00',
        'category': 'project_special',
        'tag': 'Special Project',
        'accent_color': '#22c55e',
        'stock': 50,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with default KASAUTI products'

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for data in SEED_PRODUCTS:
            obj, is_new = Product.objects.update_or_create(
                product_id=data['product_id'],
                defaults=data,
            )
            if is_new:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done! {created} products created, {updated} products updated.'
            )
        )
