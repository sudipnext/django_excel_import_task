from django.db import models

# Create your models here.
class Logs(models.Model):
    LEVEL_CHOICES = [
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARNING', 'WARNING'),
        ('ERROR', 'ERROR'),
        ('CRITICAL', 'CRITICAL'),
    ]

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    message = models.TextField()
    task_name = models.CharField(max_length=255)
    traceback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.level} - {self.message} - {self.task_name}"

    class Meta:
        verbose_name = 'Log'
        verbose_name_plural = 'Logs'

class Product(models.Model):
    AVAILABILITY_CHOICES = [
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('preorder', 'Preorder'),
    ]
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('used', 'Used'),
        ('refurbished', 'Refurbished'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
    ]
    product_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(default="")
    link = models.URLField(default="")
    image_link = models.URLField(default="")
    availability = models.CharField(max_length=50, choices=AVAILABILITY_CHOICES, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="EUR")
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES, blank=True)
    brand = models.CharField(max_length=100, blank=True)
    gtin = models.CharField(max_length=100, blank=True)
    # Recommended fields
    additional_image_links = models.JSONField(null=True, blank=True)
    shipping = models.CharField(max_length=50, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price_currency = models.CharField(max_length=3, default="EUR", null=True, blank=True)
    item_group_id = models.CharField(max_length=100, null=True, blank=True)
    google_product_category = models.CharField(max_length=255, null=True, blank=True)
    product_type = models.CharField(max_length=255, null=True, blank=True)
    size = models.CharField(max_length=50, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    material = models.CharField(max_length=100, null=True, blank=True)
    pattern = models.CharField(max_length=100, null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    #Optional fields
    product_length = models.CharField(max_length=50, null=True, blank=True)
    product_width = models.CharField(max_length=50, null=True, blank=True)
    product_height = models.CharField(max_length=50, null=True, blank=True)
    product_weight = models.CharField(max_length=50, null=True, blank=True)
    lifestyle_image_link = models.URLField(null=True, blank=True)
    max_handling_time = models.IntegerField(null=True, blank=True)
    is_bundle = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        

class ImportAnalytics(models.Model):
    file_name = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_records = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    warning_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    time_taken = models.FloatField(null=True, blank=True)  # in seconds
    status = models.CharField(max_length=20)  # processing, completed, failed

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Import {self.id} - {self.file_name}"

    class Meta:
        verbose_name = 'Import Analytics'
        verbose_name_plural = 'Import Analytics'