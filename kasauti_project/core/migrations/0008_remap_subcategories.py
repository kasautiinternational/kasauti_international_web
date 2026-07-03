from django.db import migrations


def remap_forward(apps, schema_editor):
    """Move existing products onto the new category/subcategory structure:
      - Rolls 'dtf'         -> 'single_matte'
      - Rolls 'sublimation' -> moves to the new 'sublimation_paper' category
                               (subcategory cleared so it lands on the default sub-box)
    Powder ('standard'/'premium') and blank subcategories are left untouched."""
    Product = apps.get_model('core', 'Product')

    # Old DTF rolls -> Single Matte
    Product.objects.filter(category='dtf_rolls', subcategory='dtf').update(subcategory='single_matte')

    # Old Sublimation Rolls -> new Sublimation Paper category
    Product.objects.filter(category='dtf_rolls', subcategory='sublimation').update(
        category='sublimation_paper', subcategory=''
    )


def remap_backward(apps, schema_editor):
    """Best-effort reverse (so the migration is reversible)."""
    Product = apps.get_model('core', 'Product')
    Product.objects.filter(category='dtf_rolls', subcategory='single_matte').update(subcategory='dtf')
    Product.objects.filter(category='sublimation_paper').update(category='dtf_rolls', subcategory='sublimation')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_catalogrequest_alter_product_category_and_more'),
    ]

    operations = [
        migrations.RunPython(remap_forward, remap_backward),
    ]
