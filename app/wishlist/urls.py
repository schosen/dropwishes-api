"""
URL mappings for the recipe app.
"""

from django.urls import (
    path,
    include,
)

from rest_framework.routers import DefaultRouter

from wishlist import views


router = DefaultRouter()
router.register('wishlists', views.WishlistViewSet)
router.register('products', views.ProductViewSet)

app_name = 'wishlist'

urlpatterns = [
    path('', include(router.urls)),
]
