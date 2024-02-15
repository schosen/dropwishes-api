"""
Test for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime
from core import models


def create_user(email="user@example.com", password="testpass123"):
    """Create a return a new user."""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is successful."""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "test123")

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "test123",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_wishlist(self):
        """Test creating a wishlist is successful."""
        user = get_user_model().objects.create_user(
            "test@example.com",
            "test123",
        )
        wishlist = models.Wishlist.objects.create(
            user=user,
            title="Sample wishlist",
            description="this is a test wishlist description",
            occasion_date=datetime.date(year=2020, month=1, day=1),
            address="123 Sample Street, Sampleland, 12QW 6ER",
        )

        self.assertEqual(str(wishlist), wishlist.title)

    # def test_create_product(self):
    #     """Test creating an product is successful."""
    #     user = create_user()
    #     wishlist = models.Wishlist.objects.create(
    #         user=user,
    #         title="Sample wishlist",
    #         description="this is a test wishlist description",
    #         occasion_date=datetime.date(year=2020, month=1, day=1),
    #         address="123 Sample Street, Sampleland, 12QW 6ER",
    #     )

    #     product = models.Product.objects.create(
    #         wishlist=wishlist, name="Product1", price=Decimal("5.50")
    #     )

    #     self.assertEqual(str(product), product.name)
