"""
URL mapping for user API
"""

from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('authors', views.AuthorViewSet)
router.register('products', views.ProductViewSet)

app_name = 'product'

urlpatterns = [
    path('', include(router.urls)),
]
