"""
Test for product API
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal

from product.models import Product
from product.serializers import (
    ProductSerializer,
    ProductDetailSerializer,
)


PRODUCT_URL = reverse('product:product-list')


def detail_url(product_id):
    """Create and return product detail url."""
    return reverse('product:product-detail', args=[product_id])


def create_user(**kwargs):
    """Create, update and return dict with default user data"""
    default = {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'name': 'Testname'
    }
    default.update(**kwargs)
    return get_user_model().objects.create_user(**default)


def create_product(user, **kwargs):
    """Create and return a sample product."""
    default = {
        'name': 'Test product',
        'price': Decimal('5.25')
    }
    default.update(**kwargs)
    return Product.objects.create(user=user, **default)


class PublicProductApiTests(TestCase):
    """Test public features of the product API"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(PRODUCT_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PrivateProductApiTests(TestCase):
    """Test the private features of the product API"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_products(self):
        """Test retrieving a list of products is successful."""
        create_product(user=self.user)
        create_product(user=self.user)

        res = self.client.get(PRODUCT_URL)
        products = Product.objects.all().order_by('-id')
        serializer = ProductSerializer(products, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_product_list_limited_to_user(self):
        """Test list of products is limited to authenticated user."""

        other_user = create_user(email='othertest2@example.com')
        create_product(user=other_user)
        create_product(user=self.user)

        res = self.client.get(PRODUCT_URL)

        products = Product.objects.filter(user=self.user)
        serializer = ProductSerializer(products, many=True)

        self.assertEqual(products.count(), 1)
        self.assertEqual(res.data, serializer.data)

    def test_get_product_detail(self):
        """Test get product detail is successful."""
        product = create_product(user=self.user)
        url = detail_url(product.id)

        serializer = ProductDetailSerializer(product)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_product(self):
        """Test creating product is successful."""

        payload = {
            'name': 'Test name'
        }
        res = self.client.post(PRODUCT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(product, k), v)
        self.assertEqual(product.user, self.user)

    def test_partial_update(self):
        """Test partial update of a products is successful."""
        name = 'Test name'
        update_name = 'Updated name'

        product = create_product(name=name, user=self.user)
        url = detail_url(product.id)
        res = self.client.patch(url, data={'name': update_name})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, update_name)
        self.assertEqual(product.user, self.user)

    def test_full_update(self):
        """Test full update of a product is succesful."""
        product = create_product(user=self.user)
        payload = {
            'name': 'Full update name',
            'price': Decimal('8.44')
        }

        url = detail_url(product.id)

        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(product, k), v)
        self.assertEqual(product.user, self.user)

    def test_update_user_return_error(self):
        new_user = create_user(email='test2user@example.com')
        product = create_product(user=self.user)
        payload = {
            'user': new_user
        }
        url = detail_url(product.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        product.refresh_from_db()
        self.assertEqual(product.user, self.user)

    def test_delete_product(self):
        """Test deleting product is successful."""
        product = create_product(user=self.user)
        url = detail_url(product.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=product.id))

    def test_product_other_users_delete_error(self):
        """Test trying to delete another users product gives error."""
        new_user = create_user(email='newuser@example.com')
        product = create_product(user=new_user)
        url = detail_url(product.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(Product.objects.filter(id=product.id).exists())
