from django.contrib import admin
from core.models import Product, ImportAnalytics, Logs
# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'product_id', 'brand', 'price', 'availability', 'created_at')
    search_fields = ('title', 'description', 'product_id', 'brand')
    list_filter = ('availability', 'condition', 'brand', 'created_at')

@admin.register(ImportAnalytics)
class ImportAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'status', 'total_records', 'success_count', 'warning_count', 'failure_count', 'time_taken', 'created_at')
    search_fields = ('file_name',)
    list_filter = ('status', 'created_at')

@admin.register(Logs)
class LogsAdmin(admin.ModelAdmin):
    list_display = ('level', 'message', 'task_name', 'traceback')
    search_fields = ('message', 'task_name')
    list_filter = ('level', 'task_name')
