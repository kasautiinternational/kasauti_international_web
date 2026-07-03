from django.db import migrations


def set_default_subcategories(apps, schema_editor):
    """Give existing Rolls/Powder products a sensible default sub-type so the
    new 2-box drill-down works immediately. You can re-assign some to
    'sublimation' / 'premium' later in the admin. Ink is left blank."""
    Product = apps.get_model('core', 'Product')
    Product.objects.filter(category='dtf_rolls', subcategory='').update(subcategory='dtf')
    Product.objects.filter(category='dtf_powder', subcategory='').update(subcategory='standard')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_product_subcategory_stocknotification'),
    ]

    operations = [
        migrations.RunPython(set_default_subcategories, noop),
    ]
