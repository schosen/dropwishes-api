"""
Serializers for wishlist APIs
"""

from rest_framework import serializers

from core.models import Wishlist, Product
from django.core.files.base import ContentFile
import base64
import uuid


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""

    image = serializers.CharField(
        # write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Product
        fields = ["id", "name", "link", "priority", "price", "notes", "image"]
        read_only_fields = ["id"]

    def validate_image(self, image):
        """Decode base64 image and convert it to file."""
        if (
            image is not None
            and isinstance(image, str)
            and image.startswith('data:image')
        ):
            # Decode base64 image
            format, imgstr = image.split(';base64,')
            ext = format.split('/')[-1]
            # Create a new file
            image = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return image

    ## modify create method to handle base64-encoded images
    # def create(self, validated_data):
    #     """Create a product with optional base64 image."""

    #     image_data = validated_data.pop('image', None)
    #     user = self.context['request'].user
    #     product = Product.objects.create(user=user, **validated_data)

    #     # if image_data:
    #     if (
    #         image_data is not None
    #         and isinstance(image_data, str)
    #         and image_data.startswith('data:image')
    #     ):
    #         # Decode base64 image and save it
    #         format, imgstr = image_data.split(';base64,')
    #         ext = format.split('/')[-1]
    #         product.image.save(
    #             f'{uuid.uuid4()}.{ext}',
    #             ContentFile(base64.b64decode(imgstr)),
    #             save=True,
    #         )

    #     return product


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to products."""

    class Meta:
        model = Product
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlists."""

    products = ProductSerializer(many=True, required=False)

    class Meta:
        model = Wishlist
        fields = ["id", "title", "occasion_date", "products"]
        read_only_fields = ["id"]

    def _get_or_create_products(self, products, wishlist):
        """Handle getting or creating products as needed."""
        auth_user = self.context['request'].user
        for product in products:
            product_obj, created = Product.objects.get_or_create(
                user=auth_user,
                **product,
            )
            wishlist.products.add(product_obj)

    # customize method so that we can override the
    # frameworks create/write method to create products via wishlist
    # rather than just read only on products
    def create(self, validated_data):
        """Create a wishlist."""
        products = validated_data.pop('products', [])
        wishlist = Wishlist.objects.create(**validated_data)
        self._get_or_create_products(products, wishlist)

        return wishlist

    def update(self, instance, validated_data):
        """Update wishlist."""
        products = validated_data.pop('products', None)
        if products is not None:
            if len(products) == 0:
                instance.products.clear()
                self._get_or_create_products(products, instance)
            else:
                self._get_or_create_products(products, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class WishlistDetailSerializer(WishlistSerializer):
    """Serializer for wishlist detail view."""

    class Meta(WishlistSerializer.Meta):
        fields = WishlistSerializer.Meta.fields + ["description", "address"]
