# Generated by Django 5.2 on 2025-05-09 02:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_product_currency_product_sale_price_currency_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='importanalytics',
            options={'verbose_name': 'Import Analytics', 'verbose_name_plural': 'Import Analytics'},
        ),
        migrations.AlterModelOptions(
            name='logs',
            options={'verbose_name': 'Log', 'verbose_name_plural': 'Logs'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
    ]
