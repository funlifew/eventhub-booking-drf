from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.utils import timezone

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .selectors import get_user_by_login
from .services import blacklist_all_refresh_tokens


class UserProfileSerializer(serializers.ModelSerializer):
    is_email_verified = serializers.BooleanField(
        read_only=True,
    )
    
    class Meta:
        model = User
        
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'bio',
            'avatar',
            'is_email_verified',
            'date_joined',
            'updated_at',
        )
        
        read_only_fields = (
            "id",
            "email",
            "is_email_verified",
            "date_joined",
            "updated_at",
        )
    
    def validate_username(self, value):
        value = value.strip()

        queryset = User.objects.filter(
            username__iexact=value,
        )
        
        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk,
            )
        
        if queryset.exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        
        return value

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    class Meta:
        model = User
        
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
        )
    
    def validate_username(self, value):
        value = value.strip()

        if User.objects.filter(
            username__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        
        return value
    
    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(
            email__iexact=value,
        ).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        
        return value
    
    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError(
                {
                    "password_confirm": (
                        "Passwords do not match."
                    )
                }
            )
        
        temporary_user = User(
            username=attrs.get("username", ""),
            email=attrs.get("email", ""),
            first_name=attrs.get('first_name', ""),
            last_name=attrs.get('last_name', ""),
        )
        
        try:
            validate_password(
                password,
                user=temporary_user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {
                    "password": list(exc.messages)
                }
            ) from exc
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop(
            "password_confirm"
        )
        
        password = validated_data.pop(
            "password"
        )
        
        return User.objects.create_user(
            password=password,
            is_active=False,
            **validated_data,
        )

class LoginSerializer(serializers.Serializer):
    login = serializers.CharField(
        write_only=True,
    )
    
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    def validate(self, attrs):
        login = attrs['login']
        password = attrs['password']

        user = get_user_by_login(login)

        if user is None:
            # Perform password hashing work even when the user does not exists.
            User().set_password(password)

            raise AuthenticationFailed(
                "Invalid login credentials."
            )
        
        if not user.check_password(password):
            raise AuthenticationFailed(
                "Invalid login credentials."
            )
        
        if not user.is_active:
            if not user.is_email_verified:
                raise AuthenticationFailed(
                    "Your account has not been activated."
                )
            
            raise AuthenticationFailed(
                "This account has been disabled."
            )
        
        refresh = RefreshToken.for_user(user)

        refresh['username'] = user.username
        refresh['email'] = user.email
        
        user.last_login = timezone.now()

        user.save(
            update_fields=['last_login'],
        )
        
        return {
            "access": str(
                refresh.access_token
            ),
            "refresh": str(refresh),
            "user": UserProfileSerializer(
                user,
                context=self.context,
            ).data,
        }
    

class ResendActivationSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()
    

class LogoutSerializer(
    serializers.Serializer
):
    refresh = serializers.CharField(
        write_only=True,
    )
    
    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        
        except TokenError as exc:
            raise serializers.ValidationError(
                "Invalid or expired refresh token."
            ) from exc
        
        request = self.context['request']

        try:
            token_user_id = token['user_id']
        
        except KeyError as exc:
            raise serializers.ValidationError(
                "Invalid refresh token."
            ) from exc
        
        if str(token_user_id) != str(request.user.pk):
            raise serializers.ValidationError(
                "This refresh token does not belong "
                "to the authenticated user."
            )
        
        self.token = token
        
        return value
    
    def save(self, **kwargs):
        self.token.blacklist()

class ChangePasswordSerializer(
    serializers.Serializer
):
    old_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        
        if not user.check_password(value):
            raise serializers.ValidationError(
                "Current password is incorrect."
            )
        
        return value
    
    def validate(self, attrs):
        new_password = attrs['new_password']
        new_password_confirm = attrs['new_password_confirm']

        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {
                    'new_password_confirm': (
                        'Passwords do not match.'
                    )
                }
            )
        
        user = self.context['request'].user
        
        try:
            validate_password(
                new_password,
                user=user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {
                    'new_password': list(
                        exc.messages
                    )
                }
            ) from exc
        
        return attrs
    
    def save(self, **kwargs):
        user = self.context['request'].user
        
        user.set_password(
            self.validated_data[
                'new_password'
            ]
        )
        
        user.save(
            update_fields=['password'],
        )
        
        blacklist_all_refresh_tokens(user)

        return user
    
class PasswordResetRequestSerializer(
    serializers.Serializer
):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()

class PasswordResetConfirmSerializer(
    serializers.Serializer
):
    new_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    new_password_confirm = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    
    def validate(self, attrs):
        new_password = attrs[
            'new_password'
        ]
        
        new_password_confirm = attrs[
            'new_password_confirm'
        ]
        
        if new_password != new_password_confirm:
            raise serializers.ValidationError(
                {
                    'new_password_confirm': (
                        "Passwords do not match."
                    )
                }
            )
        
        user = self.context['user']

        try:
            validate_password(
                new_password,
                user=user,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                {
                    'new_password': list(
                        exc.messages
                    )
                }
            ) from exc
        
        return attrs
    
    def save(self, **kwargs):
        user = self.context['user']

        user.set_password(
            self.validated_data[
                'new_password'
            ]
        )
        
        user.save(
            update_fields=['password'],
        )
        
        blacklist_all_refresh_tokens(user)

        return user
