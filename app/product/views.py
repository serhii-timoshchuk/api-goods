"""
Views for the product API
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from product.models import Product, Author
from product import serializers


class ProductViewSet(viewsets.ModelViewSet):
    """View for manage product APIs."""
    serializer_class = serializers.ProductDetailSerializer
    queryset = Product.objects.all()
    authentication_classes = []
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve products for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.ProductSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new product."""
        serializer.save(user=self.request.user)


class AuthorViewSet(viewsets.ModelViewSet):
    """Views for manage author APIs."""
    serializer_class = serializers.AuthorSerializer
    queryset = Author.objects.all()
    authentication_classes = []
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve authors for authenticated users."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        """Create a new author"""
        serializer.save(user=self.request.user)
