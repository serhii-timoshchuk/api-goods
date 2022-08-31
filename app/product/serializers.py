"""
Serializers for product API
"""

from rest_framework import serializers

from product.models import Product, Author


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product"""

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'createdon']
        read_only_fields = ['id', 'createdon']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view"""

    class Meta(ProductSerializer.Meta):
        pass


class AuthorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Author
        fields = ['id', 'name']
        read_only_fields = ['id']
