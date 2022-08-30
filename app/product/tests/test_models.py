"""
Test for product models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from product.models import Product, Gallery, gallery_path, Author
from django.db.utils import IntegrityError
import datetime
from unittest import mock
from django.core.files.storage import Storage


def default_data(**kwargs):
    """Create, update and return dict with default product data"""
    default = {
        'name': 'Test product',
        'price': 2.54
    }
    if kwargs:
        default.update(**kwargs)
    return default


class ProductModelTests(TestCase):
    """Test for product model"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            name='Test name',
            email='email@example.com',
            password='testpassword123'
        )

        self.default_data = default_data(user=self.user)

    def test_crete_product_error_without_user(self):
        """Test can`t create product without user."""
        del self.default_data['user']

        with self.assertRaises(IntegrityError):
            Product.objects.create(**self.default_data)

    def test_create_product_successful(self):
        """Test creating product is successful."""
        Product.objects.create(**self.default_data)

        exists = Product.objects.get(name=self.default_data['name'])
        self.assertNotEqual(exists, None)

    def test_can_create_product_without_price(self):
        """Test creating product without price is successful"""
        del self.default_data['price']

        Product.objects.create(**self.default_data)
        product = Product.objects.get(name=self.default_data['name'])
        self.assertNotEqual(product, None)
        self.assertEqual(product.price, 0.00)

    def test_createdon_exists(self):
        """Test created product contains createdon
         field equals to datetime type"""

        product = Product.objects.create(**self.default_data)
        self.assertIsInstance(product.createdon, datetime.datetime)


class GalleryModelTests(TestCase):
    """Tests for gallery model"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            name='Test name',
            email='email@example.com',
            password='testpassword123'
        )
        self.default_data = default_data(user=self.user)
        self.product = Product.objects.create(**self.default_data)

        self.image_name = 'test_image.jpg'
        self.image_field_mock = mock.MagicMock(name='get_db_prep_save')
        self.image_field_mock.return_value = self.image_name

        self.storage_mock = mock.MagicMock(spec=Storage, name='StorageMock')
        self.storage_mock.url = mock.MagicMock(name='url')
        self.storage_mock.url.return_value = '/tmp/test_image.jpg'

    def test_error_create_image_without_product(self):
        """Test creating image without product raises IntegrityError."""
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.storage_mock):
            with mock.patch('django.db.models.ImageField.get_db_prep_save',
                            self.image_field_mock):
                with self.assertRaises(IntegrityError):
                    Gallery.objects.create(image=self.image_name,
                                           user=self.user)

    def test_create_image_successful(self):
        """Test creating image for product is successful."""
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.storage_mock):
            with mock.patch('django.db.models.ImageField.get_db_prep_save',
                            self.image_field_mock):
                Gallery.objects.create(image=self.image_name,
                                       product=self.product, user=self.user)
                image = Gallery.objects.get(product=self.product)
                self.assertNotEqual(image, None)
                self.assertEqual(image.image, self.image_name)

    def test_delete_all_images_on_delete_product(self):
        """Test creating image without product raises IntegrityError."""
        with mock.patch('django.core.files.storage.default_storage._wrapped',
                        self.storage_mock):
            with mock.patch('django.db.models.ImageField.get_db_prep_save',
                            self.image_field_mock):
                Gallery.objects.create(image=self.image_name,
                                       product=self.product, user=self.user)
                Gallery.objects.create(image=self.image_name,
                                       product=self.product, user=self.user)

                count = Gallery.objects.filter(product=self.product).count()
                self.assertEqual(count, 2)

                Product.objects.get(id=self.product.id).delete()

                exists = Gallery.objects.filter(product=self.product).exists()

                self.assertFalse(exists)

    def test_gallery_image_path(self):
        """Test generating image path."""
        file_name = 'example.jpg'
        file_path = gallery_path(Gallery(product=self.product), file_name)

        self.assertEqual(file_path, f'gallery/{self.product.id}/{file_name}')


class AuthorModelTests(TestCase):
    """Test for author model"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            name='Test name',
            email='email@example.com',
            password='testpassword123'
        )
        self.author_test_name = 'Test name'

    def test_create_author_success(self):
        """Test creating author is successful."""
        Author.objects.create(user=self.user, name=self.author_test_name)
        author_form_db = Author.objects.get(name=self.author_test_name)

        self.assertNotEqual(author_form_db, None)
        self.assertEqual(author_form_db.user, self.user)

    def test_cant_create_author_without_user(self):
        """Test creating author without user raises IntegrityError"""
        with self.assertRaises(IntegrityError):
            Author.objects.create(name=self.author_test_name)
