"""
Views for the user API.
"""

from rest_framework import generics, authentication, permissions, status
from rest_framework.views import APIView

from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    ChangePasswordSerializer,
    ChangeEmailSerializer,
)
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from django.contrib.auth import update_session_auth_hash
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Change password for the authenticated user."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        """update password aand auth token"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # update session with new auth hash
        update_session_auth_hash(request, user)

        # if using drf authtoken, create a new token
        if hasattr(user, 'auth_token'):
            user.auth_token.delete()
        token, created = Token.objects.get_or_create(user=user)
        # return new token
        return Response({'token': token.key}, status=status.HTTP_200_OK)


class ChangeEmailView(generics.UpdateAPIView):
    """Change email for the authenticated user."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangeEmailSerializer

    def get_object(self):
        """Return user object"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        """update password"""
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'detail': 'Email updated successfully.'},
            status=status.HTTP_200_OK,
        )


class SoftDeleteUserView(generics.DestroyAPIView):
    """Soft delete the authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return user object"""
        return self.request.user

    def perform_destroy(self, instance):
        """Set is active to false and return response"""
        # Perform soft delete by setting is_active to False
        instance.is_active = False
        instance.save()
        return Response(
            {'detail': 'user deleted'},
            status=status.HTTP_204_NO_CONTENT,
        )


class LogoutView(APIView):
    """Logout authenticated user."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        """Remove auth token and return response"""
        # delete the token to force a login
        request.user.auth_token.delete()
        return Response(status=status.HTTP_200_OK)
