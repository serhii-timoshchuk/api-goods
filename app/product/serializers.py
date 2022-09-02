"""
Serializers for product API
"""

from rest_framework import serializers
from product.models import Product, Author, Gallery


class ProductGallerySerializer(serializers.ModelSerializer):
    """Serializer for gallery"""
    image = serializers.ImageField(use_url=True)

    class Meta:
        model = Gallery
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'False'}}


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for author"""

    class Meta:
        model = Author
        fields = ['id', 'name']
        read_only_fields = ['id']
        # extra_kwargs = {'name': {'required': 'True'}}


class BaseProductSerializer(serializers.ModelSerializer):
    """Serializer for Product"""
    author = AuthorSerializer(many=False, required=False)
    images = serializers.ListField(
        child=serializers.ImageField(max_length=None, allow_empty_file=True),
        allow_empty=True, min_length=None, max_length=None, required=False)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'createdon', 'author', 'images']
        read_only_fields = ['id', 'createdon']
        extra_kwargs = {'name': {'required': 'True'}}

    def _get_or_create_author(self, author, product):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        if author:
            author_obj, created = Author.objects.get_or_create(
                    user=auth_user,
                    **author
                )
            product.author = author_obj
            product.save()

        # Product.objects.filter(id=product.id,user=auth_user).update(author=author_obj)

    def _create_gallery_images(self, images, product):
        """Handle creating gallery images as needed."""
        for image in images:
            Gallery.objects.create(product=product, image=image)

    def create(self, validated_data):
        """Create a product"""
        author = validated_data.pop('author', {})
        images = validated_data.pop('images', [])
        product = Product.objects.create(**validated_data)
        self._get_or_create_author(author, product)
        self._create_gallery_images(images, product)
        return product

    def update(self, instance, validated_data):
        """Update product."""
        author = validated_data.pop('author', None)
        images = validated_data.pop('images', None)

        if author is not None:
            if instance.author is not None:
                instance.author.delete()
                instance.refresh_from_db()
            self._get_or_create_author(author, instance)

        if images is not None:
            gallery_exist = Gallery.objects.filter(product=instance.id)
            if gallery_exist.exists():
                gallery_exist.delete()

            self._create_gallery_images(images, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ProductGetSerializer(BaseProductSerializer):
    """Serializer for product detail view"""
    images = ProductGallerySerializer(many=True, required=False)

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields


class ProductChangeSerializer(BaseProductSerializer):
    """Serializer for product detail view"""

    class Meta(BaseProductSerializer.Meta):
        fields = BaseProductSerializer.Meta.fields
