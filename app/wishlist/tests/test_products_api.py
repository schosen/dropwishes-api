"""
Tests for the products API.
"""

import datetime
import tempfile
import os

from PIL import Image
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Product,
    Wishlist,
)

from wishlist.serializers import ProductSerializer


PRODUCTS_URL = reverse('wishlist:product-list')


def image_upload_url(product_id):
    """Create and return an image upload URL."""
    return reverse('wishlist:product-upload-image', args=[product_id])


def product_detail_url(product_id):
    """Create and return a product detail url."""
    return reverse('wishlist:product-detail', args=[product_id])


def wishlist_detail_url(wishlist_id):
    """Create and return a wishlist detail URL."""
    return reverse("wishlist:wishlist-detail", args=[wishlist_id])


def create_user(email="user@example.com", password="testpass123"):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


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


def create_product(user, **params):
    """Create and return a product."""
    defaults = {
        "name": "Sample product",
        "price": Decimal("5.99"),
        "priority": "HIGH",
        "link": "https://youtube.com",
        "notes": "smaple notes",
    }
    defaults.update(params)
    product = Product.objects.create(user=user, **defaults)
    return product


class PublicProductsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving products."""
        res = self.client.get(PRODUCTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateProductsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_products(self):
        """Test retrieving a list of products."""
        Product.objects.create(user=self.user, name="Pink Top", price=10.99)
        Product.objects.create(user=self.user, name="Sneakers", price=45.00)

        res = self.client.get(PRODUCTS_URL)

        products = Product.objects.all().order_by('-name')
        serializer = ProductSerializer(products, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_products_limited_to_user(self):
        """Test list of products is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Product.objects.create(user=user2, name="lipstick", price=10.99)
        product = Product.objects.create(
            user=self.user, name="Dress", price=45.00
        )

        res = self.client.get(PRODUCTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], product.name)
        self.assertEqual(res.data[0]['id'], product.id)

    def test_partial_update_product(self):
        """Test updating a product."""
        product = Product.objects.create(
            user=self.user, name="Pink Top", price=10.99
        )

        payload = {'name': 'Green Top'}
        url = product_detail_url(product.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, payload['name'])

    def test_delete_product(self):
        """Test deleting a product."""
        product = create_product(user=self.user)

        url = product_detail_url(product.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        products = Product.objects.filter(user=self.user)
        self.assertFalse(products.exists())

    def test_update_user_returns_error(self):
        """Test changing the product's user results in an error."""
        new_user = create_user(email="user2@example.com", password="test123")

        product = create_product(user=self.user)

        payload = {"user": new_user.id}
        url = product_detail_url(product.id)
        self.client.patch(url, payload)

        product.refresh_from_db()
        self.assertEqual(product.user, self.user)

    def test_delete_other_users_product_error(self):
        """Test trying to delete another users product gives error."""
        new_user = create_user(email="user2@example.com", password="test123")

        product = create_product(user=new_user)

        url = product_detail_url(product.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Product.objects.filter(id=product.id).exists())

    def test_create_other_users_product_error(self):
        """Test trying to create another users product gives error."""
        new_user = create_user(email="user2@example.com", password="test123")

        wishlist = create_wishlist(user=new_user)

        url = wishlist_detail_url(wishlist.id)

        payload = {
            "name": "Sample product",
            "price": Decimal("5.99"),
            "priority": "HIGH",
            "link": "https://youtube.com",
            "notes": "smaple notes",
        }

        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Product.objects.filter(name=payload["name"]).exists())

    def test_filter_products_assigned_to_wishlists(self):
        """Test listing products to those assigned to wishlists."""
        product1 = Product.objects.create(
            user=self.user, name="Orange Top", price=10.99
        )
        product2 = Product.objects.create(
            user=self.user, name="Blue Trousers", price=50.99
        )
        wishlist = Wishlist.objects.create(
            title='Bday',
            user=self.user,
            description="Sample description",
            occasion_date=datetime.date(year=2020, month=1, day=1),
            address="123 Sample Street, Sampleland, 12QW 6ER",
        )
        wishlist.products.add(product1)

        res = self.client.get(PRODUCTS_URL, {'assigned_only': 1})

        s1 = ProductSerializer(product1)
        s2 = ProductSerializer(product2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_products_unique(self):
        """Test filtered products returns a unique list."""
        product = Product.objects.create(
            user=self.user, name="Blue Trousers", price=50.99
        )
        Product.objects.create(user=self.user, name="Orange Top", price=10.99)
        wishlist1 = Wishlist.objects.create(
            title='Graduation',
            user=self.user,
            description="Sample description",
            occasion_date=datetime.date(year=2020, month=1, day=1),
            address="123 Sample Street, Sampleland, 12QW 6ER",
        )
        wishlist2 = Wishlist.objects.create(
            title='Wedding',
            user=self.user,
            description="The Big day",
            occasion_date=datetime.date(year=2020, month=1, day=1),
            address="456 Lala land, Sampleland, 890j0R",
        )
        wishlist1.products.add(product)
        wishlist2.products.add(product)

        res = self.client.get(PRODUCTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        # self.wishlist = create_wishlist(user=self.user)
        self.product = create_product(user=self.user)

    def tearDown(self):
        self.product.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a product."""
        url = image_upload_url(self.product.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.product.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.product.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image."""
        url = image_upload_url(self.product.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
