"""
Serializers for wishlist APIs
"""

from rest_framework import serializers

from core.models import Wishlist, Product


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products."""

    class Meta:
        model = Product
        fields = ["id", "name", "link", "priority", "price", "notes", "image"]
        read_only_fields = ["id"]


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
    # rather than just read
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
        # TO-DO: this should have a list of wishlist items
        fields = WishlistSerializer.Meta.fields + ["description", "address"]
