# Generated by Django 5.2 on 2025-05-07 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='availability',
            field=models.CharField(blank=True, choices=[('in_stock', 'In Stock'), ('out_of_stock', 'Out of Stock'), ('preorder', 'Preorder')], max_length=50),
        ),
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='condition',
            field=models.CharField(blank=True, choices=[('new', 'New'), ('used', 'Used'), ('refurbished', 'Refurbished')], max_length=50),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='product',
            name='gtin',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='image_link',
            field=models.URLField(default=''),
        ),
        migrations.AlterField(
            model_name='product',
            name='link',
            field=models.URLField(default=''),
        ),
    ]
