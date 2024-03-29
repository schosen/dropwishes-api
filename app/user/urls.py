"""
URL mappings for the user API.
"""

from django.urls import path

from user import views


app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
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
        'delete-user/',
        views.SoftDeleteUserView.as_view(),
        name='delete-user',
    ),
    path('token/logout/', views.LogoutView.as_view(), name='logout'),
]
