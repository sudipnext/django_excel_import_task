from rest_framework import serializers
import re
from decimal import Decimal
from core.models import Product, ImportAnalytics, Logs

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

    def validate_is_bundle(self, value):
        if isinstance(value, str):
            if value.lower() == 'yes':
                return True
            elif value.lower() == 'no':
                return False
            else:
                raise serializers.ValidationError("is_bundle must be 'yes' or 'no'")
        return value


    def validate_price(self, value):
        if not value:
            return value
            
        # If value is already a Decimal, return it
        if isinstance(value, Decimal):
            return value
            
        # Handle string format "123.45 EUR"
        if isinstance(value, str):
            price_pattern = r'^(\d+(?:\.\d{1,2})?)\s([A-Z]{3})$'
            match = re.match(price_pattern, value)
            
            if not match:
                raise serializers.ValidationError(f"Price '{value}' must be in format '123.45 EUR'")
                
            amount_str, currency = match.groups()
            
            # Store the currency separately to be used in the create/update method
            self.context['currency'] = currency
            
            # Return just the decimal amount
            return Decimal(amount_str)
            
        return value

    def validate_sale_price(self, value):
        if not value:
            return value
            
        # If value is already a Decimal or None, return it
        if isinstance(value, Decimal) or value is None:
            return value
            
        # Handle string format "123.45 EUR"
        if isinstance(value, str):
            price_pattern = r'^(\d+(?:\.\d{1,2})?)\s([A-Z]{3})$'
            match = re.match(price_pattern, value)
            
            if not match:
                raise serializers.ValidationError(f"Sale price '{value}' must be in format '123.45 EUR'")
                
            amount_str, currency = match.groups()
            
            # Store the sale price currency separately
            self.context['sale_price_currency'] = currency
            
            # Return just the decimal amount
            return Decimal(amount_str)
            
        return value
    def validate_shipping(self, value):
        shipping_pattern = r'^[A-Z]{2}:\d+(\.\d{1,2})?\s[A-Z]{3}$'
        if not re.match(shipping_pattern, value):
            raise serializers.ValidationError(f"Shipping '{value}' must be in format 'DE:0.00 EUR'")
        return value

    def validate_gtin(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("GTIN must contain only digits")
        return value

    def validate_product_length(self, value):
        if not value:
            return value

        dimension_pattern = r'^\d+(\.\d+)?\s(cm|mm|m)$'
        if not re.match(dimension_pattern, value):
            raise serializers.ValidationError(f"Product length '{value}' must be in format '123 cm'")
        return value

    def validate_product_width(self, value):
        if not value:
            return value

        dimension_pattern = r'^\d+(\.\d+)?\s(cm|mm|m)$'
        if not re.match(dimension_pattern, value):
            raise serializers.ValidationError(f"Product width '{value}' must be in format '123 cm'")
        return value

    def validate_product_height(self, value):
        if not value:
            return value

        dimension_pattern = r'^\d+(\.\d+)?\s(cm|mm|m)$'
        if not re.match(dimension_pattern, value):
            raise serializers.ValidationError(f"Product height '{value}' must be in format '123 cm'")
        return value

    def validate_product_weight(self, value):
        if not value:
            return value

        weight_pattern = r'^\d+(\.\d+)?\s(kg|g)$'
        if not re.match(weight_pattern, value):
            raise serializers.ValidationError(f"Product weight '{value}' must be in format '12.79 kg'")
        return value

    def validate_max_handling_time(self, value):
        if not value:
            return value

        try:
            handling_time = int(value)
            if handling_time < 0:
                raise serializers.ValidationError("Handling time must be a positive integer")
            return handling_time  # Return the converted integer value
        except ValueError:
            raise serializers.ValidationError("Handling time must be a valid integer")

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