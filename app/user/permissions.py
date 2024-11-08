"""
Module for Custom UserPermissions
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        if obj.owner:
            # Instance must have an attribute named `owner`.
            return obj.owner == request.user
        else:
            return obj.user == request.user


class IsAdminOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):

        if request.method in permissions.SAFE_METHODS:
            return True

        return bool(request.user and request.user.is_staff)


class PublicReservePermission(permissions.BasePermission):
    """
    Allow non-authenticated users to reserve a product, but restrict other actions.
    """

    def has_permission(self, request, view):
        # Allow unauthenticated users to reserve items
        if view.action == 'reserve':
            return True

        if view.action == 'unreserve':
            return True

        # Otherwise, default to checking if the user is authenticated
        return request.user and request.user.is_authenticated
