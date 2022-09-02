"""
URL mapping for user API
"""

from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('authors', views.AuthorViewSet, basename='authors')
router.register('products', views.ProductViewSet, basename='products')

app_name = 'product'

urlpatterns = [
    path('', include(router.urls)),
    path('products/<int:id>/images/',
         views.GalleryView.as_view(),
         name='images'),

    path('products/<int:id>/images/<int:gallery_id>',
         views.GalleryDetailView.as_view(),
         name='gallery-detail'),
]
