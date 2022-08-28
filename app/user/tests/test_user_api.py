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


def user_data(**kwargs):
    """Create, update and return dict with default user data"""
    default = {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'name': 'Testname'
    }
    default.update(**kwargs)
    return default


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
        payload = user_data()

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_user_email_exists_error(self):
        """Test error returned if user email is already exists"""
        payload = user_data()
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_to_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = user_data(password='test')

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_access_token_for_user(self):
        """Test creating access token is successful."""
        payload = user_data()
        get_user_model().objects.create_user(**payload)
        del payload['name']

        res = self.client.post(reverse('user:token_obtain_pair'), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_create_refresh_token_for_user(self):
        """Test creating refresh token is successful."""
        payload = user_data()
        get_user_model().objects.create_user(**payload)
        del payload['name']

        res = self.client.post(reverse('user:token_obtain_pair'), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('refresh', res.data)

    def test_create_token_bad_credentials(self):
        """Test returns errors if credentials are invalid"""
        default = user_data()
        del default['name']
        payload1, payload2, payload3 = default, default, default
        payload1['email'] = 'wrong@example.com'
        payload2['password'] = 'wrongpassword123'
        payload3['email'] = 'wrong@example.com'
        payload3['password'] = 'wrongpassword123'

        get_user_model().objects.create_user(**user_data())

        for payload in [payload1, payload2, payload3]:
            res = self.client.post(reverse('user:token_obtain_pair'), payload)
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_error_create_token_empty_credentials(self):
        """Test returns errors if credentials are empty."""
        default = user_data()
        del default['name']
        payload1, payload2, payload3 = default, default, default
        payload1['email'] = ''
        payload2['password'] = ''
        payload3['email'] = ''
        payload3['password'] = ''

        get_user_model().objects.create_user(**user_data())

        for payload in [payload1, payload2, payload3]:
            res = self.client.post(reverse('user:token_obtain_pair'), payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
