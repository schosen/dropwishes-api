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
from django.conf import settings
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text

# from django.middleware.csrf import get_token

from core.utils import EmailUtil
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    ChangePasswordSerializer,
    ChangeEmailSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


def verification_email_data(request):
    """returns the subject, body and to email for user verification"""
    scheme = request.scheme
    token = default_token_generator.make_token(request.user)
    uidb64 = urlsafe_base64_encode(force_bytes(request.user.pk))

    client_site = settings.CLIENT_HOST

    mail_subject = 'Verify your account'
    message = f'Click the link to verify your email: {scheme}://{client_site}/auth/email-verify?uidb64={uidb64}&token={token}'  # noqa: E501
    data = {
        'email_body': message,
        'to_email': request.user.email,
        'email_subject': mail_subject,
    }
    return data


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_verified = False
        user.save()

        # Generate token for email verification
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        scheme = request.scheme
        # Send verification email

        client_site = settings.CLIENT_HOST

        mail_subject = 'Activate your account'
        message = f'Click the link to verify your email: {scheme}://{client_site}/auth/email-verify?uidb64={uidb64}&token={token}'  # noqa: E501
        # message = f'Click the link to verify your email: {scheme}://{current_site}{reverse("user:verify", kwargs={"uidb64": urlsafe_base64_encode(force_bytes(user.pk)), "token": token})}'  # noqa: E501
        send_mail(
            mail_subject, message, from_email='', recipient_list=[user.email]
        )

        # Create authentication token
        token, _ = Token.objects.get_or_create(user=user)

        response_data = {'token': token.key}
        response = Response(response_data, status.HTTP_201_CREATED)

        response.set_cookie(
            key='auth_token',
            value=token.key,
            httponly=True,
            secure=(not settings.DEBUG),  # Use True in production
            samesite='Strict',
        )

        # return Response(
        #     {
        #         'token': token.key,
        #         'message': 'Please check your email for verification',
        #     },
        #     status=status.HTTP_201_CREATED,
        # )

        return response


class UserVerificationAPIView(APIView):
    """Verify user's email via link"""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uidb64 = request.query_params.get('uidb64')
        token = request.query_params.get('token')
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            get_user_model().DoesNotExist,
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
            data = verification_email_data(request)
            EmailUtil.send_email(data=data)
            return Response(
                {'message': 'Verification link resent successfully'},
                status=status.HTTP_200_OK,
            )


class CreateTokenView(ObtainAuthToken):
    """
    Create a new auth token for user.
    Override default ObtainAuthToken view from
    rest_framework to set the token into a
    HttpOnly cookie.
    The 'secure' option will depend on the settings.DEBUG value.
    """

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        # csrf_token = get_token(request)

        # Create the response with token data
        # response_data = {'token': token.key, 'csrfToken': csrf_token}
        response_data = {'token': token.key}
        response = Response(response_data)

        # Set the token in an HTTP-only cookie
        response.set_cookie(
            key='auth_token',
            value=token.key,
            httponly=True,
            secure=(not settings.DEBUG),  # Use True in production
            samesite='Strict',
        )
        # response.set_cookie(
        #     key='csrftoken',
        #     value=csrf_token,
        #     httponly=False,
        #     secure=(not settings.DEBUG),  # Use True in production
        #     samesite='Strict',
        # )
        return response


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

        data = verification_email_data(request)
        EmailUtil.send_email(data=data)
        return Response(
            {'detail': 'Email updated successfully.'},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestAPIView(generics.CreateAPIView):
    """Reset password for user"""

    serializer_class = PasswordResetRequestSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = get_user_model().objects.get(email=email)
            # Generate password reset token
            scheme = request.scheme
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # Construct reset password link
            # current_site = get_current_site(request)

            client_site = settings.CLIENT_HOST
            reset_password_link = f'{scheme}://{client_site}/auth/reset-password?uidb64={uidb64}&token={token}'  # noqa: E501

            # reset_password_link = f'{scheme}://{current_site}{reverse("user:password_reset_confirm",kwargs={"uidb64": uid, "token": token})}'  # noqa: E501

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
    """validate token and new password"""

    serializer_class = PasswordResetConfirmSerializer

    def get(self, request):
        uidb64 = request.query_params.get('uidb64')
        token = request.query_params.get('token')
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
        # TO-DO: Dont show post form if token is invalid/returns 400 code

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data['password']
        uidb64 = request.query_params.get('uidb64')
        token = request.query_params.get('token')

        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = get_user_model().objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.set_password(password)
                user.save()
                # TO-DO invalidate token.
                # Example: TokenModel.objects.filter(user=user).delete()
                return Response(
                    {'message': 'Password reset successful'},
                    status=status.HTTP_200_OK,
                )
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
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('auth_token')
        response.delete_cookie('csrftoken')
        return response


class ValidateTokenView(APIView):
    """Validate the Auth token"""

    authentication_classes = [authentication.TokenAuthentication]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({"isAuthenticated": True})
        else:
            return Response({"isAuthenticated": False}, status=401)
