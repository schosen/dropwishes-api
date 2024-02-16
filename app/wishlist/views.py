"""
Views for the wishlist APIs
"""

from rest_framework import viewsets, mixins
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.generics import get_object_or_404


from core.models import Wishlist, Product
from wishlist import serializers


class WishlistViewSet(viewsets.ModelViewSet):
    """View for manage wishlist APIs."""

    serializer_class = serializers.WishlistDetailSerializer
    queryset = Wishlist.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve wishlists for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.WishlistSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new wishlist."""
        serializer.save(user=self.request.user)


class ProductViewSet(
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Manage products in the database."""

    serializer_class = serializers.ProductSerializer
    queryset = Product.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-name')
