"""
Tests for user model
"""
from django.test import TestCase
from django.contrib.auth import get_user_model


class UserModelTests(TestCase):
    """Test for custom user model"""

    def test_create_user_with_email(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'UserTestPassword'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        exist = get_user_model().objects.filter(email=email).exists()
        self.assertTrue(exist)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        email_samples = [
            ['Test1@example.com', 'Test1@example.com'],
            ['Test2@EXAMPLE.COM', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com']
        ]
        for email, expected in email_samples:
            user = get_user_model().objects.create_user(
                email=email,
                password='TestPassword123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test raise error on creating user without an email."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'TestPassword123')

    def test_create_super_user(self):
        """Test creating a superuser is successful."""
        email = 'superuser@example.com'
        password = 'TestPassword123'
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password
        )

        exist = get_user_model().objects.filter(email=email).exists()
        self.assertTrue(exist)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
