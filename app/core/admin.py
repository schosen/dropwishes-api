# """
# Django admin customization.
# """

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.utils.translation import gettext_lazy as _

# from core import models


# class UserAdmin(BaseUserAdmin):
#     """Define the admin pages for users."""

#     ordering = ["id"]
#     list_display = ["email", "first_name", "last_name", "uuid"]
#     fieldsets = (
#         (
#             None,
#             {
#                 "fields": (
#                     "email",
#                     "password",
#                 )
#             },
#         ),
#         (
#             _("Personal Info"),
#             {"fields": ("first_name", "last_name", "birthday", "gender")},
#         ),
#         (
#             _("Permissions"),
#             {
#                 "fields": (
#                     "is_active",
#                     "is_staff",
#                     "is_superuser",
#                 )
#             },
#         ),
#         (_("Important dates"), {"fields": ("last_login",)}),
#     )
#     readonly_fields = ["last_login"]
#     add_fieldsets = (
#         (
#             None,
#             {
#                 "classes": ("wide",),
#                 "fields": (
#                     "email",
#                     "first_name",
#                     "last_name",
#                     "password1",
#                     "password2",
#                     "birthday",
#                     "gender",
#                     "is_active",
#                     "is_staff",
#                     "is_superuser",
#                 ),
#             },
#         ),
#     )


# admin.site.register(models.User, UserAdmin)
# admin.site.register(models.Wishlist)
# admin.site.register(models.Product)
