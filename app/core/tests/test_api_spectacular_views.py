"""Tests for drf-spectacular views"""

from django.test import SimpleTestCase
from django.urls import reverse


class SpectacularTests(SimpleTestCase):
    """Test for drf-spectacular views"""

    def test_page_api_docs_exists(self):
        """Test api docs page returns 200 response to a GET request"""
        res = self.client.get(reverse('core:api-docs'))

        self.assertEqual(res.status_code, 200)
