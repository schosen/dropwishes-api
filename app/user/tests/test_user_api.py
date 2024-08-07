"""
Tests for the user API.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from rest_framework import status
from core.models import User


CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')
CHANGE_PASSWORD_URL = reverse('user:change-password')
CHANGE_EMAIL_URL = reverse('user:change-email')
DELETE_USER_URL = reverse('user:delete-user')
LOGOUT_URL = reverse('user:logout')


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the public features of the user API."""

    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            'email': 'test@example.com',
            'confirm_email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'first_name': 'John',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_create_user_with_mismatch_password_fails(self):
        """test creating user with mismatch password confirmation fails"""
        payload = {
            'email': 'test@example.com',
            'confirm_email': 'test@example.com',
            'first_name': 'John',
            'password': 'testpass123',
            'confirm_password': 'different-password',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_create_user_with_mismatch_email_fails(self):
    #     """Test creating user with mismatch email fails"""
    #     payload = {
    #         'email': 'test@example.com',
    #         'confirm_email': 'different-email@example.com',
    #         'first_name': 'John',
    #         'password': 'testpass123',
    #         'confirm_password': 'testpass123',
    #     }
    #     res = self.client.post(CREATE_USER_URL, payload)

    #     self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_without_name_failure(self):
        """Test creating a user fails when you don't add name."""
        payload = {
            'email': 'test@example.com',
            'confirm_email': 'test@example.com',
            'password': 'testpass123',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_with_email_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            'email': 'test@example.com',
            'first_name': 'John',
            'password': 'testpass123',
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'first_name': 'John',
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = (
            get_user_model().objects.filter(email=payload['email']).exists()
        )
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            # 'first_name': 'test',
            'email': 'test@example.com',
            'password': 'test-user-password123',
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(email='test@example.com', password='goodpass')

        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_email_not_found(self):
        """Test error returned if user not found for given email."""
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {'email': 'test@example.com', 'password': ''}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test Name',
            last_name='Last Name',
            gender='female',
            birthday="2023-11-15",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                'first_name': self.user.first_name,
                'email': self.user.email,
                'last_name': self.user.last_name,
                'gender': self.user.gender,
                'birthday': self.user.birthday,
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {
            'first_name': 'Updated name',
            'last_name': 'updated last name',
        }

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, payload['first_name'])
        self.assertTrue(self.user.last_name, (payload['last_name']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_password(self):
        """Test update password for authenticated user"""
        payload = {
            "old_password": "testpass123",
            "new_password1": "updated-password",
            "new_password2": "updated-password",
        }

        res = self.client.patch(CHANGE_PASSWORD_URL, payload, format='json')

        updated_user = User.objects.get(email='test@example.com')
        self.assertTrue(updated_user.check_password(payload['new_password1']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_email(self):
        """Test update email for authenticated user"""
        payload = {
            'new_email': 'updated@example.com',
            'confirm_email': 'updated@example.com',
            'password': 'testpass123',
        }

        res = self.client.put(CHANGE_EMAIL_URL, payload, format='json')
        updated_user = User.objects.get(first_name=self.user.first_name)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(updated_user.email, payload['new_email'])

    # TO-DO: add new tests
    # def test_update_email_sends_new_verification_link(self):
    # """Test changing email sends new verification link"""

    # def test_request_reset_password(self):
    # """Test request reset password sends link
    # with token and successfully submits requests"""

    def test_logout_user(self):
        """Test log out user"""
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        res = self.client.post(LOGOUT_URL)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        with self.assertRaises(Token.DoesNotExist):
            Token.objects.get(key=token.key)
        # response_after_logout = self.client.get(ME_URL)
        # self.assertEqual(
        #     response_after_logout.status_code, status.HTTP_401_UNAUTHORIZED
        # )

    def test_delete_user_soft_delete(self):
        """Test delete user soft deletes the user"""
        res = self.client.delete(DELETE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        deleted_user = User.objects.get(email='test@example.com')
        self.assertFalse(deleted_user.is_active)
