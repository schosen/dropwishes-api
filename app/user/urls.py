"""
URL mappings for the user API.
"""

from django.urls import path, include

from user import views


app_name = 'user'

urlpatterns = [
    path('', include('drfpasswordless.urls')),
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path(
        'email-verify/',
        views.UserVerificationAPIView.as_view(),
        name='verify',
    ),
    path(
        'resend-verification-link/',
        views.ResendVerificationLinkAPIView.as_view(),
        name='resend_verification_link',
    ),
    path('me/', views.ManageUserView.as_view(), name='me'),
    path(
        'change-password/',
        views.ChangePasswordView.as_view(),
        name='change-password',
    ),
    path(
        'change-email/',
        views.ChangeEmailView.as_view(),
        name='change-email',
    ),
    path(
        'reset-password/',
        views.PasswordResetRequestAPIView.as_view(),
        name='password_reset_request',
    ),
    path(
        'reset-password/confirm',
        views.PasswordResetConfirmAPIView.as_view(),
        name='password_reset_confirm',
    ),
    path(
        'delete-user/',
        views.SoftDeleteUserView.as_view(),
        name='delete-user',
    ),
    path('token/logout/', views.LogoutView.as_view(), name='logout'),
    path(
        'validate-token/',
        views.ValidateTokenView.as_view(),
        name='validate-token',
    ),
]
