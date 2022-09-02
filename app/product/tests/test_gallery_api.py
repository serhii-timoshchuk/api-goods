"""
Tests for gallery API
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from product.models import Product, Gallery
from product.serializers import ProductGallerySerializer
from unittest import mock
from django.core.files.storage import Storage

import os
from PIL import Image
import tempfile


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
    """Create and return a sample author."""
    default = {
        'name': 'Test product name'
    }
    default.update(**kwargs)
    return Product.objects.create(user=user, **default)


class PublicGalleryApiTests(TestCase):
    """Tests for public features of the gallery"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.product = create_product(user=self.user)
        self.gallery_url = reverse('product:images', args=(self.product.id,))

    def test_auth_required(self):
        """Test authentication is required"""

        res = self.client.get(self.gallery_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateGalleryApiTests(TestCase):
    """Test for private features of gallery API."""

    def setUp(self):
        self.user = create_user()
        self.product = create_product(user=self.user)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.gallery_url = reverse('product:images', args=(self.product.id,))

    def detail_url(self, gallery_id):
        """Create and return a tag detail url"""
        return reverse('product:gallery-detail', kwargs={
            'id': self.product.id,
            'gallery_id': gallery_id
        }
                       )

    def create_gallery(self, image_name='test_image.jpg', product=None):
        """Create and return gallery instance"""
        if product is None:
            product = self.product

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
                    product=product
                )

    def test_retrieve_gallery_list(self):
        """Test retrieving list of gallery images is successful"""
        self.create_gallery(image_name='test1.jpg')
        self.create_gallery(image_name='test2.jpg')

        images = Gallery.objects.all().order_by('-id')

        res = self.client.get(self.gallery_url)
        request_object = res.wsgi_request
        serializer = ProductGallerySerializer(
            images,
            many=True,
            context={'request': request_object}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_list_limited_to_product(self):
        """Test retrieving list of gallery images
         limited to particular product."""
        new_product_name = 'new product name'
        new_product = create_product(user=self.user, name=new_product_name)
        self.create_gallery(
            image_name='test1.jpg',
            product=new_product)

        self.create_gallery(image_name='test2.jpg')

        images = Gallery.objects.filter(product=self.product).order_by('-id')

        res = self.client.get(self.gallery_url)
        request_object = res.wsgi_request
        serializer = ProductGallerySerializer(
            images,
            many=True,
            context={'request': request_object})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    #
    # def test_gallery_create(self):
    #     """Test creating gallery image is successful."""
    #     url = self.gallery_url
    #     with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
    #         image = Image.new('RGB', (10, 10))
    #         image.save(image_file, format='JPEG')
    #         image_file.seek(0)
    #         payload = {'image': image_file}
    #         res = self.client.post(url, payload, format='multipart')
    #
    #     gallery = Gallery.objects.get(product=self.product)
    #     self.assertEqual(res.status_code, status.HTTP_201_CREATED)
    #     self.assertIn('image', res.data)
    #     self.assertTrue(os.path.exists(gallery.image.path))
    #
    #     gallery.image.delete()

    def test_update(self):
        """Test updating gallery image is successful."""
        gallery = self.create_gallery()
        url = self.detail_url(gallery.id)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            image = Image.new('RGB', (10, 10))
            image.save(image_file, format='JPEG')
            image_file.seek(0)

            payload = {'image': image_file}
            res = self.client.patch(url, payload, format='multipart')

        # gallery = Gallery.objects.get(product=self.product)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        gallery.refresh_from_db()
        self.assertTrue(os.path.exists(gallery.image.path))
        self.assertEqual(
            gallery.image.name.split('/')[-1],
            image_file.name.split('/')[-1])

        gallery.image.delete()

    def test_delete(self):
        """Test deleting gallery image is successful."""
        gallery = self.create_gallery()
        url = self.detail_url(gallery.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        gallery = Gallery.objects.filter(id=gallery.id).exists()
        self.assertFalse(gallery)

    def test_upload_image_bad_request(self):
        """Test uploading invalid gallery image"""
        gallery = self.create_gallery()
        url = self.detail_url(gallery.id)
        payload = {'image': 'asdd.asd'}

        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        gallery.refresh_from_db()
        gallery_exists = Gallery.objects.filter(id=gallery.id).exists()
        self.assertTrue(gallery_exists)
