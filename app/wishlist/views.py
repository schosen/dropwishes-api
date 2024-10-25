"""
Views for the wishlist APIs
"""

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from user.permissions import IsOwnerOrReadOnly, PublicReservePermission
from django.shortcuts import get_list_or_404
from django.conf import settings
from core.models import Wishlist, Product
from wishlist import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'products',
                OpenApiTypes.STR,
                description='Comma separated list of products IDs to filter',
            ),
        ]
    )
)
class WishlistViewSet(viewsets.ModelViewSet):
    """View for manage wishlist APIs."""

    serializer_class = serializers.WishlistDetailSerializer
    queryset = Wishlist.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""

        # TO-Do raise error if user imputs something other than string
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve wishlists for authenticated user."""
        products = self.request.query_params.get('products')
        queryset = self.queryset
        if products:
            product_ids = self._params_to_ints(products)
            queryset = queryset.filter(products__id__in=product_ids)

        return (
            queryset.filter(user=self.request.user).order_by('-id').distinct()
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.WishlistSerializer
        elif self.action == 'view_shared_wishlist':
            return serializers.WishlistSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new wishlist."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='generate-shared-link')
    def generate_share_link(self, request, pk=None):
        """Generates a link for users to view wishlists"""
        user = request.user

        print("REQUEST = ", request.data)
        wishlist_ids = request.data

        if not wishlist_ids:
            return Response(
                {'error': 'No wishlists selected'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        wishlists = get_list_or_404(Wishlist, id__in=wishlist_ids, user=user)

        incorrect_user = [
            element for element in wishlists if element.user != user
        ]

        if incorrect_user:
            return Response(
                {"error": "Only the owner can share the wishlist"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # for wishlist in wishlists:
        #     if wishlist.user == user:
        #         return Response(
        #             {"error": "Only the owner can share the wishlist"},
        #             status=status.HTTP_403_FORBIDDEN,
        #         )

        for wishlist in wishlists:
            wishlist.is_public = True
            wishlist.save()

        # Generate the UUID-based link that includes multiple wishlists
        scheme = request.scheme
        client_site = settings.CLIENT_HOST
        wishlist_ids_str = ','.join([str(w.id) for w in wishlists])
        share_link = f"{scheme}://{client_site}/wishlists/view/{user.uuid}/{wishlist_ids_str}"

        return Response({'shareLink': share_link})

    @action(
        detail=False,
        methods=['get'],
        url_path='view/(?P<user_uuid>[-\w]+)/(?P<wishlist_ids>[-\w,]+)',
    )
    def view_shared_wishlist(self, request, user_uuid, wishlist_ids):
        print("UUID = ", user_uuid)
        print("WISHLIST ID =", wishlist_ids)

        # Split wishlist_ids by commas
        wishlist_ids_list = wishlist_ids.split(',')

        # Filter the wishlists by ids and user uuid
        wishlists = Wishlist.objects.filter(
            id__in=wishlist_ids_list, user__uuid=user_uuid
        )

        if not wishlists.exists():
            return Response(
                {'error': 'No wishlists found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check if any wishlists are not public
        non_public_wishlists = [
            wishlist for wishlist in wishlists if not wishlist.is_public
        ]

        if non_public_wishlists:
            return Response(
                {
                    'error': 'Invalid wishlist request, contains non-public wishlists'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Serialize the wishlists to return the data
        serializer = serializers.WishlistSerializer(wishlists, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT,
                enum=[0, 1],
                description='Filter by products assigned to wishlist. 0=False, 1-True',
            ),
        ]
    )
)
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
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(wishlist__isnull=False)

        return (
            queryset.filter(user=self.request.user)
            .order_by('-name')
            .distinct()
        )

    def get_serializer_class(self):
        """upload image for authenticated user."""
        if self.action == 'upload_image':
            return serializers.ProductImageSerializer

        return self.serializer_class

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to product."""
        product = self.get_object()
        serializer = self.get_serializer(product, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[PublicReservePermission],
    )
    def reserve(self, request, pk=None):
        """
        reserve wishlist product
        """
        try:
            product = self.get_object()
            wishlist = product.wishlist

            if request.user == wishlist.owner:
                return Response(
                    {
                        "error": "Owners cannot reserve their own wishlist items"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            product.is_reserved = True

            # if request.user.is_authenticated:
            #     product.reserved_by = request.user
            # else:
            #     product.reserved_by_guest = request.data.get('guest_name', 'Guest')

            product.save()
            return Response(
                {"message": "Product reserved successfully"},
                status=status.HTTP_200_OK,
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[PublicReservePermission],
    )
    def unreserve(self, request, pk=None):
        """
        unreserve wishlist product
        """
        try:
            product = self.get_object()
            wishlist = product.wishlist

            if request.user == wishlist.owner:
                return Response(
                    {
                        "error": "Owners cannot reserve their own wishlist items"
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            product.is_reserved = False

            product.save()
            return Response(
                {"message": "Product unreserved, successfully"},
                status=status.HTTP_200_OK,
            )
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND,
            )


class MergeWishlistView(
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """manages merging wishlists made by unauthenticated users"""

    serializer_class = serializers.WishlistDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        add wishlist that is saved on users browser to backend
        """

        local_wishlists = request.data.get('wishList', None)

        if not local_wishlists:
            return Response(
                {"error": "No wishlist data provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for wishlist_data in local_wishlists:
            # Create or update the wishlist,
            # products are handled by WishlistSerializer
            wishlist_serializer = self.get_serializer(data=wishlist_data)
            wishlist_serializer.is_valid(raise_exception=True)
            wishlist_serializer.save(user=request.user)

            # for wishlist_data in local_wishlists:
            #     # Extract products data
            #     products_data = wishlist_data.pop('products', [])

            #     # Create or update the wishlist
            #     wishlist_serializer = self.get_serializer(data=wishlist_data)
            #     wishlist_serializer.is_valid(raise_exception=True)
            #     wishlist = wishlist_serializer.save(user=request.user)

            #     # Handle products creation
            #     for product_data in products_data:
            #         product_data['user'] = (
            #             request.user.id
            #         )
            # Ensure the product is linked to the authenticated user
            #         product_serializer = serializers.ProductSerializer(
            #             data=product_data, context={'request': request}
            #         )
            #         if product_serializer.is_valid():
            #             product = product_serializer.save()
            #             wishlist.products.add(product)
            #         else:
            #             return Response(
            #                 product_serializer.errors,
            #                 status=status.HTTP_400_BAD_REQUEST,
            #             )

            return Response(
                wishlist_serializer.data, status=status.HTTP_201_CREATED
            )
