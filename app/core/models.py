"""
Database models.
"""

from django.conf import settings
from django.db import models
import uuid
import os
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


def product_image_file_path(instance, filename):
    """Generate file path for new product image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'product', filename)


def blog_image_file_path(instance, filename):
    """Generate file path for new blog image."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'

    return os.path.join('uploads', 'blog', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password=None, **extra_fields):
        """Create, save and return a new user."""
        if not email:
            raise ValueError("User must have an email address.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        """Create and return a new superuser."""
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    MALE = "M"
    FEMALE = "F"
    PREFER_NOT_TO_SAY = "N"

    GENDER_CHOICES = [
        (MALE, "Male"),
        (FEMALE, "Female"),
        (PREFER_NOT_TO_SAY, "Prefer Not To Say"),
    ]

    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    last_name = models.CharField(max_length=255, blank=True)
    gender = models.CharField(
        max_length=255, choices=GENDER_CHOICES, blank=True
    )
    birthday = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"


class Wishlist(models.Model):
    """Wishlist object."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    occasion_date = models.DateField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    products = models.ManyToManyField("Product")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Product(models.Model):
    """Products for wishlist."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    PRIORITY_CHOICES = [(HIGH, "high"), (MEDIUM, "medium"), (LOW, "low")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255)
    priority = models.CharField(
        max_length=6,
        choices=PRIORITY_CHOICES,
        blank=True,
        default=PRIORITY_CHOICES[2][1],
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    link = models.URLField(max_length=255, blank=True, null=True)
    image = models.ImageField(null=True, upload_to=product_image_file_path)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    """Posts object for blog."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=100, blank=True, default='')
    body = models.TextField(blank=True, default='')
    image = models.ImageField(null=True, upload_to=blog_image_file_path)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='posts',
        on_delete=models.CASCADE,
    )
    tags = models.ManyToManyField('Tag')

    class Meta:
        ordering = ("-created_at",)


class Comment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    body = models.TextField(blank=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        'Post', related_name='comments', on_delete=models.CASCADE
    )
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies',
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.owner.first_name}'s comment: {self.body}"


class Tag(models.Model):
    """Tag for filtering blog posts."""

    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
