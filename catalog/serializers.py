# catalog/serializers.py

from rest_framework import serializers
from .models import Product, QuantityPrice,Category,SubCategory

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id','name','slug','active']

class SubCategorySerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    class Meta:
        model = SubCategory
        fields =['id','name','slug','category','active']

class QuantityPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuantityPrice
        fields = ['id', 'min_qty', 'max_qty', 'price']

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'sku', 'name', 'description', 'base_price', 'stock', 'active','subcategory']

class ProductDetailSerializer(serializers.ModelSerializer):
    quantity_prices = QuantityPriceSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ['id','sku','name','description','base_price','stock','active','quantity_prices','subcategory']
