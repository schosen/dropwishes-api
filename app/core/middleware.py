from django.utils.deprecation import MiddlewareMixin
from rest_framework.authentication import get_authorization_header
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.middleware.csrf import CsrfViewMiddleware


class CookieTokenAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware that extracts auth token from cookie and
    sets Authorization header
    """

    def process_request(self, request):
        # Extract the auth token from the cookie
        auth_token = request.COOKIES.get('auth_token')
        if auth_token:
            try:
                token = Token.objects.get(key=auth_token)
                request.user = token.user
                # Set the Authorization header for DRF to process
                request.META['HTTP_AUTHORIZATION'] = f'Token {auth_token}'
            except Token.DoesNotExist:
                raise AuthenticationFailed('Invalid token')


# class CustomCsrfViewMiddleware(CsrfViewMiddleware):
#     """
#     Middleware that extracts CSRF token from cookie
#     and sets in X_CSRFTOKEN header
#     """

#     def process_view(self, request, callback, callback_args, callback_kwargs):
#         if getattr(request, 'user', None) and request.user.is_authenticated:
#             # Extract the CSRF token from the cookie
#             csrf_token = request.COOKIES.get('csrftoken')
#             if csrf_token:
#                 # Set the CSRF token header for CSRF middleware to process
#                 request.META['HTTP_X_CSRFTOKEN'] = csrf_token
#         return super().process_view(
#             request, callback, callback_args, callback_kwargs
#         )
