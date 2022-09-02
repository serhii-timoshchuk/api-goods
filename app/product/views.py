"""
Views for the product API
"""
from rest_framework import viewsets, generics, mixins
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from product.models import Product, Author, Gallery
from product import serializers


class ProductViewSet(viewsets.ModelViewSet):
    """View for manage product APIs."""
    serializer_class = serializers.ProductChangeSerializer
    queryset = Product.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve products for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request"""
        if self.action == 'list':
            return serializers.ProductGetSerializer
        if self.action == 'retrieve':
            return serializers.ProductGetSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new product."""
        serializer.save(user=self.request.user)


class AuthorViewSet(mixins.DestroyModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    """Views for manage author APIs."""
    serializer_class = serializers.AuthorSerializer
    queryset = Author.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve authors for authenticated users."""
        return self.queryset.filter(user=self.request.user).order_by('-id')


class GalleryView(generics.ListAPIView):
    """Gallery view for GET methods"""
    queryset = Gallery.objects.all()
    serializer_class = serializers.ProductGallerySerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(product=self.kwargs['id']).order_by('-id')


# class GalleryDetailView(generics.UpdateAPIView):

class GalleryDetailView(mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    """Gallery detail view for PUT, PATCH, DELETE"""
    serializer_class = serializers.ProductGallerySerializer
    authenticated_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Gallery.objects.all()
    lookup_url_kwarg = 'gallery_id'

    def get_queryset(self):
        return self.queryset.filter(product=self.kwargs['id']).order_by('-id')

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
