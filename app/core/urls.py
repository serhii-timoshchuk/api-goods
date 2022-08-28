"""
URL mapping for core views
"""

from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = 'core'

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='core:api-schema'),
        name='api-docs'
    ),
]
