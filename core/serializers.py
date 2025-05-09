from rest_framework import serializers
import re
from decimal import Decimal
from core.models import Product, ImportAnalytics, Logs

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        # Apply the currencies extracted during validation
        if 'currency' in self.context:
            validated_data['currency'] = self.context['currency']
        if 'sale_price_currency' in self.context:
            validated_data['sale_price_currency'] = self.context['sale_price_currency']
            
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Apply the currencies extracted during validation
        if 'currency' in self.context:
            validated_data['currency'] = self.context['currency']
        if 'sale_price_currency' in self.context:
            validated_data['sale_price_currency'] = self.context['sale_price_currency']
            
        return super().update(instance, validated_data)


class ImportAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportAnalytics
        fields = '__all__'

class LogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Logs
        fields = '__all__'