"""
Test for author API
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from product.models import Author
from product.serializers import AuthorSerializer


AUTHOR_URL = reverse('product:author-list')


def detail_url(author_id):
    """Create and return product detail url."""
    return reverse('product:author-detail', args=[author_id])


def create_user(**kwargs):
    """Create, update and return dict with default user data"""
    default = {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'name': 'Testname'
    }
    default.update(**kwargs)
    return get_user_model().objects.create_user(**default)


def create_author(user, **kwargs):
    """Create and return a sample author."""
    default = {
        'name': 'Test author name'
    }
    default.update(**kwargs)
    return Author.objects.create(user=user, **default)


class PublicAuthorApiTests(TestCase):
    """Test for public features of author API"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AUTHOR_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PrivateAuthorApiTests(TestCase):
    """Test for private features of author API"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_author_list(self):
        """Test retrieving list of authors is successful"""
        create_author(user=self.user)
        create_author(user=self.user)

        authors = Author.objects.all().order_by('-id')
        serializer = AuthorSerializer(authors, many=True)
        res = self.client.get(AUTHOR_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieving_list_limited_to_user(self):
        """Test retrieving list of authors limited to particular user."""
        new_user = create_user(email='newuser@example.com')
        create_author(user=self.user)
        create_author(user=new_user)

        authors = Author.objects.filter(user=self.user)
        serializer = AuthorSerializer(authors, many=True)
        res = self.client.get(AUTHOR_URL)

        self.assertEqual(res.data, serializer.data)
        self.assertEqual(authors.count(), 1)

    def test_get_author_detail(self):
        """Test get author detail is successful"""
        author_name = 'New author name'
        author = create_author(user=self.user, name=author_name)
        url = detail_url(author.id)

        res = self.client.get(url)
        serializer = AuthorSerializer(author)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], author_name)
        self.assertEqual(res.data, serializer.data)

    def test_author_create(self):
        """Test creating author is successful."""
        payload = {'name': 'new author name'}

        res = self.client.post(AUTHOR_URL, payload)

        author = Author.objects.get(name=payload['name'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(author, None)
        self.assertEqual(author.user, self.user)

    def test_particular_update(self):
        """Test particular update is successful."""
        name = 'Author name'
        author = create_author(name=name, user=self.user)
        update_name = 'Update name'
        payload = {
            'name': update_name
        }
        url = detail_url(author.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        author.refresh_from_db()
        self.assertEqual(author.name, update_name)
        self.assertEqual(author.user, self.user)

    def test_full_update(self):
        """Test full update is successful."""
        name = 'Author name'
        author = create_author(name=name, user=self.user)
        update_name = 'Update name'
        payload = {
            'name': update_name
        }
        url = detail_url(author.id)

        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        author.refresh_from_db()
        self.assertEqual(author.name, update_name)
        self.assertEqual(author.user, self.user)

    def test_delete(self):
        """Test deleting author is successful."""
        author = create_author(user=self.user)
        url = detail_url(author.id)

        res = self.client.delete(url)
        authors = Author.objects.filter(user=self.user)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(authors)

    def test_author_other_user_delete_error(self):
        """Test deleting author of the other users raises error."""
        new_user = create_user(email='newuser@example.com')
        author = create_author(user=new_user)

        url = detail_url(author)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        author_exists = Author.objects.filter(user=new_user).exists()
        self.assertTrue(author_exists)
