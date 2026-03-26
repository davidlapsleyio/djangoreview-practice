import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from authentication.models import PasswordResetToken, UserProfile

User = get_user_model()


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/auth/register/"

    def test_register_success(self):
        """Test successful user registration."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123",
            "password_confirm": "strongpass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        """Test registration fails when passwords don't match."""
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "strongpass123",
            "password_confirm": "differentpass",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/auth/login/"
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_login_success(self):
        """Test successful login returns tokens."""
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)

    def test_login_invalid_credentials(self):
        """Test login fails with wrong password."""
        data = {"username": "testuser", "password": "wrongpassword"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_with_remember_me(self):
        """Test login with remember_me flag."""
        data = {
            "username": "testuser",
            "password": "testpass123",
            "remember_me": True,
        }
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = UserProfile.objects.get(user=self.user)
        self.assertTrue(profile.remember_me_token)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.reset_url = "/api/auth/password-reset/"
        self.confirm_url = "/api/auth/password-reset/confirm/"
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_request_password_reset(self):
        """Test requesting a password reset token."""
        data = {"email": "test@example.com"}
        response = self.client.post(self.reset_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())

    def test_confirm_password_reset(self):
        """Test confirming a password reset with a valid token."""
        token = PasswordResetToken.objects.create(
            user=self.user, token=PasswordResetToken.generate_token()
        )
        data = {
            "token": token.token,
            "new_password": "newstrongpass456",
            "new_password_confirm": "newstrongpass456",
        }
        response = self.client.post(self.confirm_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # Issue 10: No tests for expired tokens, brute force, or edge cases


class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/auth/login/"
        self.refresh_url = "/api/auth/token/refresh/"
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_refresh_token(self):
        """Test refreshing an access token."""
        # First login to get tokens
        login_data = {"username": "testuser", "password": "testpass123"}
        login_response = self.client.post(self.login_url, login_data, format="json")
        refresh_token = login_response.data["refresh_token"]

        # Use refresh token to get new access token
        data = {"refresh_token": refresh_token}
        response = self.client.post(self.refresh_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
