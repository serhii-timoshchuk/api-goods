"""
Tests for product API
"""
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from decimal import Decimal

import tempfile
from PIL import Image
from unittest import mock
from django.core.files.storage import Storage

from product.models import Product, Author, Gallery
from product.serializers import ProductGetSerializer as ProductSerializer


PRODUCT_URL = reverse('product:products-list')


def detail_url(product_id):
    """Create and return product detail url."""
    return reverse('product:products-detail', args=[product_id])


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

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProductApiTests(TestCase):
    """Test the private features of the product API"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def create_gallery(self, image_name='test_image.jpg', product=None):
        """Create and return gallery instance"""
        if product is None:
            product = create_product(user=self.user)

        self.image_name = image_name
        self.image_field_mock = mock.MagicMock(name='get_db_prep_save')
        self.image_field_mock.return_value = self.image_name

        self.storage_mock = mock.MagicMock(spec=Storage, name='StorageMock')
        self.storage_mock.url = mock.MagicMock(name='url')
        self.storage_mock.url.return_value = '/tmp/' + self.image_name

        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.storage_mock):
            with mock.patch('django.db.models.ImageField.get_db_prep_save',
                            self.image_field_mock):
                return Gallery.objects.create(
                    image=self.image_name,
                    product=product)

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

        serializer = ProductSerializer(product)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_product(self):
        """Test creating product is successful."""

        payload = {
            'name': 'Test name',
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

    def test_create_product_with_new_author(self):
        """Test creating a product with new author is successful."""
        payload = {
            'name': 'Test product name',
            'author': {'name': 'New author'}
        }

        res = self.client.post(PRODUCT_URL, payload, format='json')
        author_exist = Author.objects.filter(user=self.user).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(author_exist)

        author = Author.objects.get(user=self.user)
        self.assertEqual(author.name, payload['author']['name'])

    def test_create_product_with_existing_author(self):
        """Test creating a product with existing author is successful."""
        existing_author_name = 'Author already exists'
        exist_author = Author.objects.create(
            user=self.user,
            name=existing_author_name
        )

        payload = {
            'name': 'Test product name',
            'author': {'name': existing_author_name}
        }

        res = self.client.post(PRODUCT_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        authors = Author.objects.filter(user=self.user)
        self.assertEqual(authors.count(), 1)
        product = Product.objects.get(user=self.user)
        self.assertEqual(product.author, exist_author)

    def test_create_author_on_update(self):
        """Test creating author on product update is successful."""
        product = create_product(user=self.user)
        payload = {
            'author': {'name': 'New author'}
        }

        url = detail_url(product.id)
        res = self.client.patch(url, payload, format='json')
        author_exists = Author.objects.filter(
            user=self.user,
            name=payload['author']['name']
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(author_exists.exists())
        product.refresh_from_db()
        self.assertEqual(product.author.name, payload['author']['name'])

    def test_update_product_assign_author(self):
        """Test assigning an existing author when update a product."""
        firts_author = Author.objects.create(
            user=self.user,
            name='First Author'
        )
        second_author = Author.objects.create(
            user=self.user,
            name='Second Author'
        )
        product = create_product(user=self.user, author=firts_author)
        payload = {
            'author': {'name': second_author.name}
        }

        url = detail_url(product.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.author, second_author)

    def test_clear_product_author(self):
        """Test clearing a product author."""
        author = Author.objects.create(user=self.user, name='Author name')
        product = create_product(user=self.user, author=author)

        payload = {
            'author': {}
        }
        url = detail_url(product.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertIsNone(product.author)

    def test_create_product_with_new_gallery_images(self):
        """Test creating a product with new author is successful."""
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10, 10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {
                'name': 'Test product name111',
                'images_to_load': [image_file]
            }

            res = self.client.post(PRODUCT_URL, payload, format='multipart')
        product_id = res.data['id']
        gallerys = Gallery.objects.filter(product=product_id)
        self.assertTrue(gallerys.exists())
        self.assertEqual(gallerys.count(), 1)
        for gallery_item in gallerys:
            gallery_item.image.delete()

    def test_create_gallery_images_on_update(self):
        """Test creating author on product update is successful."""
        product = create_product(user=self.user)
        url = detail_url(product.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10, 10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {
                       'images_to_load': [image_file]
                       }
            res = self.client.patch(url, payload, format='multipart')

        gallery_exists = Gallery.objects.filter(product=product)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(gallery_exists.exists())
        self.assertEqual(gallery_exists.count(), 1)

    def test_clear_product_gallery_images(self):
        """Test clearing a product author."""
        gallery = self.create_gallery()
        url = detail_url(gallery.product.id)

        payload = {
            'asdasd': 'asd',
            'images_to_load': []

        }

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        galerry_exist = Gallery.objects.filter(id=gallery.id).exists()
        self.assertFalse(galerry_exist)
