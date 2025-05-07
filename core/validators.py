from pydantic import BaseModel, validator
from typing import Optional
from enum import Enum
import re

class Availability(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PREORDER = "preorder"
    BACKORDER = "backorder"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"


class Condition(str, Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"


class YesNo(str, Enum):
    YES = "yes"
    NO = "no"


class ProductValidator(BaseModel):
    # Mandatory fields
    id: str
    title: str
    image_link: str
    description: str
    link: str
    price: str
    availability: Availability
    brand: str
    gtin: str
    condition: Condition

    # Recommended fields
    sale_price: Optional[str] = None
    item_group_id: Optional[str] = None
    google_product_category: Optional[str] = None
    product_type: Optional[str] = None
    shipping: Optional[str] = None
    additional_image_links: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    pattern: Optional[str] = None
    gender: Optional[Gender] = None
    Model: Optional[str] = None

    # Optional fields
    product_length: Optional[str] = None
    product_width: Optional[str] = None
    product_height: Optional[str] = None
    product_weight: Optional[str] = None
    lifestyle_image_link: Optional[str] = None
    max_handling_time: Optional[str] = None
    is_bundle: Optional[str] = None

    @validator('id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("ID must be a non-empty string")
        return v

    @validator('title')
    def validate_title(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Title must be a non-empty string")
        if len(v) > 150:
            raise ValueError("Title must not exceed 150 characters")
        return v

    @validator('image_link', 'link', 'lifestyle_image_link')
    def validate_url(cls, v):
        if v is None:
            return v

        if not v.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {v}")
        return v

    @validator('price', 'sale_price')
    def validate_price(cls, v):
        if v is None:
            return v

        price_pattern = r'^\d+(\.\d{1,2})?\s[A-Z]{3}$'
        if not re.match(price_pattern, v):
            raise ValueError(f"Price '{v}' must be in format '123.45 EUR'")
        return v

    @validator('shipping')
    def validate_shipping(cls, v):
        if v is None:
            return v

        shipping_pattern = r'^[A-Z]{2}:\d+(\.\d{1,2})?\s[A-Z]{3}$'
        if not re.match(shipping_pattern, v):
            raise ValueError(f"Shipping '{v}' must be in format eg: 'DE:0.00 EUR' (country:price)")
        return v

    @validator('availability')
    def validate_availability(cls, v):
        valid_values = ['in_stock', 'out_of_stock', 'preorder', 'backorder']
        if v.lower() not in valid_values:
            raise ValueError(f"Availability must be one of: {', '.join(valid_values)}")
        return v.lower()

    @validator('additional_image_links')
    def validate_additional_images(cls, v):
        if v is None:
            return v

        urls = v.split(',')
        for url in urls:
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL in additional_image_links: {url}")
        return v

    @validator('gtin')
    def validate_gtin(cls, v):
        if not v.isdigit():
            raise ValueError("GTIN must contain only digits")
        return v


    @validator('product_length', 'product_width', 'product_height')
    def validate_dimensions(cls, v):
        if v is None:
            return v

        dimension_pattern = r'^\d+(\.\d+)?\s(cm|mm|m)$'
        if not re.match(dimension_pattern, v):
            raise ValueError(f"Dimension '{v}' must be in format '123 cm'")
        return v

    @validator('product_weight')
    def validate_weight(cls, v):
        if v is None:
            return v

        weight_pattern = r'^\d+(\.\d+)?\s(kg|g)$'
        if not re.match(weight_pattern, v):
            raise ValueError(f"Weight '{v}' must be in format '12.79 kg'")
        return v

    @validator('max_handling_time')
    def validate_handling_time(cls, v):
        if v is None:
            return v

        try:
            handling_time = int(v)
            if handling_time < 0:
                raise ValueError("Handling time must be a positive integer")
        except ValueError:
            raise ValueError("Handling time must be a valid integer")
        return v

    @validator('is_bundle')
    def validate_is_bundle(cls, v):
        if v is None:
            return v

        valid_values = ['yes', 'no']
        if v.lower() not in valid_values:
            raise ValueError(f"is_bundle must be one of: {', '.join(valid_values)}")
        return v.lower()

    @validator('condition')
    def validate_condition(cls, v):
        valid_values = ['new', 'used', 'refurbished']
        if v.lower() not in valid_values:
            raise ValueError(f"Condition must be one of: {', '.join(valid_values)}")
        return v.lower()


def validate_product_row(row_data):
    """
    Validate a row of product data and return errors if any

    Args:
        row_data (dict): Dictionary containing product data fields

    Returns:
        tuple: (is_valid, errors)
            - is_valid (bool): True if valid, False otherwise
            - errors (dict): Dictionary of field-specific errors if any
    """
    try:
        ProductValidator(**row_data)
        return True, {}
    except Exception as e:
        # Extract validation errors
        if hasattr(e, 'errors'):
            errors = {}
            for error in e.errors():
                field = error['loc'][0]
                message = error['msg']
                errors[field] = message
            return False, errors
        else:
            return False, {"general": str(e)}
