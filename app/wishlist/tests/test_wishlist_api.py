"""
Tests for wishlist APIs.
"""

import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Wishlist, Product


from wishlist.serializers import (
    WishlistSerializer,
    WishlistDetailSerializer,
)

WISHLIST_URL = reverse("wishlist:wishlist-list")


def wishlist_detail_url(wishlist_id):
    """Create and return a wishlist detail URL."""
    return reverse("wishlist:wishlist-detail", args=[wishlist_id])


def create_wishlist(user, **params):
    """Create and return a sample wishlist."""
    defaults = {
        "title": "Sample wishlist title",
        "description": "Sample description",
        "occasion_date": datetime.date(year=2020, month=1, day=1),
        "address": "123 Sample Street, Sampleland, 12QW 6ER",
    }
    defaults.update(params)

    wishlist = Wishlist.objects.create(user=user, **defaults)
    return wishlist


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicWishlistAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(WISHLIST_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateWishlistApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email="user@example.com", password="test123")
        self.client.force_authenticate(self.user)

    def test_retrieve_wishlist(self):
        """Test retrieving a list of wishlist."""
        create_wishlist(user=self.user)
        create_wishlist(user=self.user)

        res = self.client.get(WISHLIST_URL)

        wishlist = Wishlist.objects.all().order_by("-id")
        serializer = WishlistSerializer(wishlist, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_wishlist_list_limited_to_user(self):
        """Test list of wishlist is limited to authenticated user."""
        other_user = create_user(email="other@example.com", password="test123")

        create_wishlist(user=other_user)
        create_wishlist(user=self.user)

        res = self.client.get(WISHLIST_URL)

        wishlist = Wishlist.objects.filter(user=self.user)
        serializer = WishlistSerializer(wishlist, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_wishlist_detail(self):
        """Test get wishlist detail."""
        wishlist = create_wishlist(user=self.user)

        url = wishlist_detail_url(wishlist.id)
        res = self.client.get(url)

        serializer = WishlistDetailSerializer(wishlist)
        self.assertEqual(res.data, serializer.data)

    def test_clear_wishlist_products(self):
        """Test clearing a wishlists products."""

        payload = {
            "title": "Sample wishlist",
            "description": "Sample description",
            "occasion_date": datetime.date(year=2020, month=1, day=1),
            "address": "123 Sample Street, Sampleland, 12QW 6ER",
            "products": [
                {"name": "Pink Top", "price": 10.99},
                {"name": "Sneakers", "price": 45.00},
            ],
        }
        wishlist = self.client.post(WISHLIST_URL, payload, format="json")

        update_payload = {"products": []}
        url = wishlist_detail_url(wishlist.data["id"])
        res = self.client.patch(url, update_payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["products"]), 0)

    def test_create_product_on_update(self):
        """Test create product when updating a wishlist."""
        wishlist = create_wishlist(user=self.user)
        payload = {"products": [{"name": "Pink Top", "price": 10.99}]}
        url = wishlist_detail_url(wishlist.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_product = Product.objects.get(
            wishlist=wishlist.id, name="Pink Top"
        )
        self.assertIn(new_product, wishlist.products.all())

    def test_create_product_on_update_adds_to_existing_product_list(self):
        """
        Test creating a new product on update adds
        to existing list of products
        """
        payload = {
            "title": "Sample wishlist",
            "description": "Sample description",
            "occasion_date": datetime.date(year=2020, month=1, day=1),
            "address": "123 Sample Street, Sampleland, 12QW 6ER",
            "products": [
                {"name": "Pink Top", "price": 10.99},
                {"name": "Sneakers", "price": 45.00},
            ],
        }
        wishlist = self.client.post(WISHLIST_URL, payload, format="json")
        update_payload = {"products": [{"name": "Purse", "price": 20.00}]}
        url = wishlist_detail_url(wishlist.data["id"])
        res = self.client.patch(url, update_payload, format="json")
        wishlist_products = Product.objects.filter(
            wishlist=wishlist.data["id"]
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(wishlist_products.count(), 3)
        self.assertTrue(
            wishlist_products.filter(
                name=update_payload["products"][0]["name"],
                wishlist=wishlist.data["id"],
            ).exists()
        )
        for product in payload["products"]:
            exists = wishlist_products.filter(
                name=product["name"],
                wishlist=wishlist.data["id"],
            ).exists()
            self.assertTrue(exists)

    def test_create_product_on_update_on_other_user_error(self):
        """
        Test create product when updating a wishlist
        on another users wishlist gives error.
        """
        new_user = create_user(email="user2@example.com", password="test123")
        wishlist = create_wishlist(user=new_user)
        payload = {"products": [{"name": "Pink Top", "price": 10.99}]}

        url = wishlist_detail_url(wishlist.id)
        res = self.client.patch(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            Product.objects.filter(
                id=wishlist.id, name=payload["products"][0]["name"]
            ).exists()
        )

    def test_create_wishlist_with_new_products(self):
        """Test creating a wishlist with new products."""

        payload = {
            "title": "Sample wishlist",
            "description": "Sample description",
            "occasion_date": datetime.date(year=2020, month=1, day=1),
            "address": "123 Sample Street, Sampleland, 12QW 6ER",
            "products": [
                {"name": "Pink Top", "price": 10.99},
                {"name": "Sneakers", "price": 45.00},
            ],
        }
        res = self.client.post(WISHLIST_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        wishlists = Wishlist.objects.filter(user=self.user)
        self.assertEqual(wishlists.count(), 1)
        wishlist = wishlists[0]
        self.assertEqual(wishlist.products.count(), 2)
        for product in payload["products"]:
            exists = wishlist.products.filter(
                name=product["name"],
                wishlist=wishlist,
            ).exists()
            self.assertTrue(exists)

    def test_create_wishlist(self):
        """Test creating a wishlist."""
        payload = {
            "title": "Sample wishlist",
            "description": "Sample description",
            "occasion_date": datetime.date(year=2020, month=1, day=1),
            "address": "123 Sample Street, Sampleland, 12QW 6ER",
        }
        res = self.client.post(WISHLIST_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        wishlist = Wishlist.objects.get(id=res.data["id"])
        for k, v in payload.items():
            self.assertEqual(getattr(wishlist, k), v)
        self.assertEqual(wishlist.user, self.user)

    def test_partial_update(self):
        """Test partial update of a wishlist."""
        original_address = "123 Sample Street, Sampleland, 12QW 6ER"
        wishlist = create_wishlist(
            user=self.user,
            title="Sample wishlist title",
            occasion_date=datetime.date(year=2020, month=1, day=1),
            address=original_address,
        )

        payload = {"title": "New wishlist title"}
        url = wishlist_detail_url(wishlist.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        wishlist.refresh_from_db()
        self.assertEqual(wishlist.title, payload["title"])
        self.assertEqual(wishlist.address, original_address)
        self.assertEqual(wishlist.user, self.user)

    def test_full_update(self):
        """Test full update of wishlist."""
        wishlist = create_wishlist(
            user=self.user,
            title="Sample wishlist title",
            address="123 Sample Street, Sampleland, 12QW 6ER",
            description="Sample wishlist description.",
        )

        payload = {
            "title": "New wishlist title",
            "address": "456 New Sample Street, Sampleland, 12QW 6ER",
            "description": "New wishlist description",
            "occasion_date": datetime.date(year=2023, month=9, day=10),
        }
        url = wishlist_detail_url(wishlist.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        wishlist.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(wishlist, k), v)
        self.assertEqual(wishlist.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the wishlist user results in an error."""
        new_user = create_user(email="user2@example.com", password="test123")
        wishlist = create_wishlist(user=self.user)

        payload = {"user": new_user.id}
        url = wishlist_detail_url(wishlist.id)
        self.client.patch(url, payload)

        wishlist.refresh_from_db()
        self.assertEqual(wishlist.user, self.user)

    def test_delete_wishlist(self):
        """Test deleting a wishlist successful."""
        wishlist = create_wishlist(user=self.user)

        url = wishlist_detail_url(wishlist.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Wishlist.objects.filter(id=wishlist.id).exists())

    def test_wishlist_delete_other_users_wishlist_error(self):
        """Test trying to delete another users wishlist gives error."""
        new_user = create_user(email="user2@example.com", password="test123")
        wishlist = create_wishlist(user=new_user)

        url = wishlist_detail_url(wishlist.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Wishlist.objects.filter(id=wishlist.id).exists())


# "TO-DO: CREATE API FOR USER TO DELETE ALL WISHLISTS"
