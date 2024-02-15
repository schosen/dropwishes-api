"""
Database models.
"""

from django.conf import settings
from django.db import models
import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)


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
    NONBINARY = "N"

    GENDER_CHOICES = [
        (MALE, "Male"),
        (FEMALE, "Female"),
        (NONBINARY, "Non Binary"),
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
    # image = models.ImageField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.name
