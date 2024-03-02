"""
Serializers for the user API View.
"""

from django.contrib.auth import (
    get_user_model,
    authenticate,
    password_validation,
)
from django.utils.translation import gettext as _

from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    # email_verify and password field to verify email and password, unsure if this will work
    confirm_email = serializers.EmailField(required=True, write_only=True)
    confirm_password = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    # make password and email read only on update
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            # if object is being created the instance doesn't exist yet, otherwise it exists.
            # therefore we can make read only for updates
            self.fields.get('email').read_only = True
            self.fields.get('password').read_only = True

    class Meta:
        model = get_user_model()
        fields = [
            'email',
            'confirm_email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'gender',
            'birthday',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'confirm_password': {'write_only': True, 'min_length': 6},
        }

    # def validate(self, data):
    # TO-DO: read-only fields return code 200 need to raise validation error for them
    # return data

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        if validated_data['password'] != validated_data['confirm_password']:
            raise serializers.ValidationError(
                {
                    'confirm_password': _(
                        "The two password fields didn't match."
                    )
                }
            )
        password_validation.validate_password(
            validated_data['password'], self.context['request'].user
        )

        if validated_data['email'] != validated_data['confirm_email']:
            raise serializers.ValidationError(
                {'confirm_email': _("The two email fields didn't match.")}
            )

        # remove confirm_email and confirm_password fields
        validated_data.pop('confirm_email', None)
        validated_data.pop('confirm_password', None)

        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user."""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials.')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer to change password"""

    old_password = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )
    new_password1 = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )
    new_password2 = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                _(
                    'Your old password was entered incorrectly. Please enter it again.'
                )
            )
        return value

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError(
                {'new_password2': _("The two password fields didn't match.")}
            )
        password_validation.validate_password(
            data['new_password1'], self.context['request'].user
        )
        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password1']
        user = self.context['request'].user
        user.set_password(password)
        user.save()
        return user


class ChangeEmailSerializer(serializers.Serializer):
    """Serializer to change email"""

    new_email = serializers.EmailField(
        max_length=255,
        required=True,
    )
    confirm_email = serializers.EmailField(
        max_length=255,
        required=True,
    )

    password = serializers.CharField(
        max_length=128,
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
        required=True,
    )

    def validate(self, data):
        user = self.context['request'].user

        # Validate password
        password = data.get('password')
        if not user.check_password(password):
            raise serializers.ValidationError(_("Incorrect password."))

        # Validate new email and confirmation
        new_email = data.get('new_email')
        confirm_email = data.get('confirm_email')
        if new_email != confirm_email:
            raise serializers.ValidationError(
                _("New email and confirmation do not match.")
            )
        return data

    def save(self, **kwargs):
        email = self.validated_data['new_email']
        user = self.context['request'].user
        user.email = email
        user.save()
        return user
