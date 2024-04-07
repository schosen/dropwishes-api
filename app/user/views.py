"""
Views for the user API.
"""

from rest_framework import generics, authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import update_session_auth_hash, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text

# from core.utils import EmailUtil
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    ChangePasswordSerializer,
    ChangeEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # user.is_active = False  # User is inactive until email confirmation
        user.is_verified = False
        user.save()

        # Generate token for email verification
        token = default_token_generator.make_token(user)
        scheme = request.scheme
        # Send verification email
        current_site = get_current_site(request)
        mail_subject = 'Activate your account'
        message = f'Click the link to verify your email: {scheme}://{current_site}{reverse("user:activate", kwargs={"uidb64": urlsafe_base64_encode(force_bytes(user.pk)), "token": token})}'  # noqa: E501
        send_mail(
            mail_subject, message, from_email='', recipient_list=[user.email]
        )

        return Response(
            {'message': 'Please check your email for verification'},
            status=status.HTTP_201_CREATED,
        )


class UserVerificationAPIView(generics.GenericAPIView):
    """Verify user's email link"""

    permission_classes = [permissions.AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            get_user_model.DoesNotExist,
        ):
            user = None
        if user is not None and default_token_generator.check_token(
            user, token
        ):
            if user.is_verified:
                return Response(
                    {'message': 'User is already verified'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                user.is_verified = True
                user.save()
                # TO-DO Invalidate the token
                # You can delete the token from the database or mark it as used, depending on your implementation # noqa: E501
                return Response(
                    {'message': 'Your account has been verified'},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {'message': 'Invalid verification link'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationLinkAPIView(generics.GenericAPIView):
    """Resent user verification link by email"""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.is_verified:
            return Response(
                {'message': 'Your account is already verified'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            # Generate token for email verification
            token = default_token_generator.make_token(request.user)

            # Resend verification email
            current_site = get_current_site(request)
            mail_subject = 'Verify your account'
            message = f'Click the link to verify your email: http://{current_site}{reverse("user:activate", kwargs={"uidb64": urlsafe_base64_encode(force_bytes(request.user.pk)), "token": token})}'  # noqa: E501
            send_mail(
                mail_subject,
                message,
                from_email='',
                recipient_list=[request.user.email],
            )
            return Response(
                {'message': 'Verification link resent successfully'},
                status=status.HTTP_200_OK,
            )


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


class PasswordResetRequestAPIView(generics.CreateAPIView):
    serializer_class = PasswordResetRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = get_user_model().objects.get(email=email)
            # Generate password reset token
            scheme = request.scheme
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # Construct reset password link
            current_site = get_current_site(request)
            # reset_password_link = request.build_absolute_uri(
            #     f'/api/user/reset-password/confirm/{uid}/{token}/'
            # )

            reset_password_link = f'{scheme}://{current_site}{reverse("user:password_reset_confirm",kwargs={"uidb64": uid, "token": token})}'  # noqa: E501

            # Send email with password reset link
            subject = 'Password Reset'
            message = f'Follow this link to reset your password: {reset_password_link}'  # noqa: E501
            # TO-DO make token expire after some time
            # Logic to send email
            send_mail(subject, message, None, [email])
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK,
            )
        except get_user_model().DoesNotExist:
            pass  # Handle case where email doesn't exist without leaking information # noqa: E501
        return Response(
            {'error': 'User with this email does not exist'},
            status=status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetConfirmAPIView(generics.CreateAPIView):
    serializer_class = PasswordResetConfirmSerializer

    def get(self, request, uidb64, token):
        try:
            # Decode the uidb64 and validate the token
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                return Response(
                    {'message': 'Token is valid'}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'message': 'Invalid token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (
            TypeError,
            ValueError,
            OverflowError,
            get_user_model().DoesNotExist,
        ):
            return Response(
                {'message': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request, uidb64, token):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        # confirm_password = serializer.validated_data['confirm_password']
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                # if password == confirm_password:
                user.set_password(password)
                user.save()
                # TO-DO invalidate token.
                # Example: TokenModel.objects.filter(user=user).delete()
                return Response(
                    {'message': 'Password reset successful'},
                    status=status.HTTP_200_OK,
                )
                # else:
                #     raise ValidationError('Passwords do not match')
            else:
                return Response(
                    {'error': 'Invalid link'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
                # raise ValidationError('Invalid token')
        except (
            TypeError,
            ValueError,
            OverflowError,
            get_user_model().DoesNotExist,
        ):
            return Response(
                {'error': 'Invalid request'},
                status=status.HTTP_400_BAD_REQUEST,
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
