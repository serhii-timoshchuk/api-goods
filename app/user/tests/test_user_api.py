"""
Test for user API
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('user:create')


def create_user(**kwargs):
    """Create and return user"""
    return get_user_model().objects.create_user(**kwargs)


class PublicUserApiTests(TestCase):
    """Tests the public features of the user API"""

    def setUp(self):
        self.client = APIClient()

    def test_empty_post_request_raise_error(self):
        """Test empty POST request raise error"""
        payload = {}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_success(self):
        """Test creating user is successful."""
        payload = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'name': 'Testname'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_email_exists_error(self):
        """Test error returned if user email is already exists"""
        payload = {
            'email': 'test@example.com',
            'password': 'testpassword123',
            'name': 'Testname'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_to_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'email': 'test@example.com',
            'password': 'test',
            'name': 'Testname'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)
