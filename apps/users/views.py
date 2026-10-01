from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.db import transaction
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.throttling import (
    ScopedRateThrottle,
)
from rest_framework.views import APIView

from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .selectors import (
    get_user_by_email,
    get_user_from_uid,
)
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ResendActivationSerializer,
    UserProfileSerializer,
)
from .services import (
    send_activation_email,
    send_password_reset_email,
)
from .tokens import account_activation_token

class RegisterView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(
            data=request.data
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        with transaction.atomic():
            user = serializer.save()

            transaction.on_commit(
                lambda: send_activation_email(
                    request=request,
                    user=user,
                )
            )
        
        return Response(
            {
                "message": (
                    "Account created successfully. "
                    "Please check your email to "
                    "activate your account."
                ),
                "user": UserProfileSerializer(
                    user,
                    context={
                        'request': request,
                    },
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )

class ActivateAccountView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle,
    ]
    throttle_scope = 'activation'

    def get(
        self,
        request,
        uidb64,
        token,
    ):
        user = get_user_from_uid(
            uidb64
        )
        
        if user is None:
            return Response(
                {
                    "detail": (
                        "Invalid activation link."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if user.is_active:
            return Response(
                {
                    "message": (
                        "Account is already active."
                    )
                },
                status=status.HTTP_200_OK,
            )
        
        if user.is_email_verified:
            return Response(
                {
                    "detail": (
                        "This email has already been "
                        "verified, but the account "
                        "is currently disabled."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not account_activation_token.check_token(
            user,
            token,
        ):
            return Response(
                {
                    "detail": (
                        "Activation link is invalid "
                        "or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        user.is_active = True
        user.email_verified_at = timezone.now()
        
        user.save(
            update_fields=[
                'is_active',
                'email_verified_at',
            ]
        )
        
        return Response(
            {
                "message": (
                    "Account activated successfully. "
                    "You can now log in."
                )
            },
            status=status.HTTP_200_OK,
        )

class ResendActivationView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle,
    ]

    throttle_scope = "resend_activation"

    def post(self, request):
        serializer = (
            ResendActivationSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        user = get_user_by_email(
            serializer.validated_data[
                "email"
            ]
        )

        if (
            user is not None
            and not user.is_active
            and not user.is_email_verified
        ):
            send_activation_email(
                request=request,
                user=user,
            )

        # IMPORTANT:
        # This return is OUTSIDE the if.
        return Response(
            {
                "message": (
                    "If an inactive account exists "
                    "for this email, an activation "
                    "email has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class LoginView(APIView):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle,
    ]
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK,
        )

class RefreshTokenView(
    TokenRefreshView
):
    throttle_classes = [
        ScopedRateThrottle,
    ]
    throttle_scope = "token_refresh"

class VerifyTokenView(
    TokenVerifyView
):
    pass

class LogoutView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
    
    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data,
            context={
                'request': request,
            },
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        serializer.save()

        return Response(
            {
                "message": (
                    "Logged out successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

class MeView(
    generics.RetrieveUpdateAPIView
):
    permission_classes = [
        IsAuthenticated,
    ]
    
    serializer_class = (
        UserProfileSerializer
    )
    
    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]
    
    def post(self, request):
        serializer = (
            ChangePasswordSerializer(
                data=request.data,
                context={
                    'request': request,
                },
            )
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        serializer.save()

        return Response(
            {
                "message": (
                    "Password changed successfully. "
                    "Please log in again."
                )
            },
            status=status.HTTP_200_OK,
        )

class PasswordResetRequestView(
    APIView
):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle,
    ]
    throttle_scope = 'password_reset'

    def post(self, request):
        serializer = (
            PasswordResetRequestSerializer(
                data=request.data,
            )
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        user = get_user_by_email(
            serializer.validated_data["email"]
        )
        
        if (
            user is not None
            and user.is_active
        ):
            send_password_reset_email(
                request=request,
                user=user,
            )
        
        return Response(
            {
                "message": (
                    "If an active account exists "
                    "for this email, a password "
                    "reset email has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )

class PasswordResetConfirmView(
    APIView
):
    permission_classes = [AllowAny]

    throttle_classes = [
        ScopedRateThrottle,
    ]
    throttle_scope = 'password_reset_confirm'

    def post(
        self,
        request,
        uidb64,
        token,
    ):
        user = get_user_from_uid(
            uidb64
        )
        
        if (
            user is None
            or not user.is_active
            or not (
                default_token_generator
                .check_token(
                    user,
                    token,
                )
            )
        ):
            return Response(
                {
                    "detail": (
                        "Password reset link is "
                        "invalid or has expired."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        
        serializer = (
            PasswordResetConfirmSerializer(
                data=request.data,
                context={
                    "user": user,
                },
            )
        )
        
        serializer.is_valid(
            raise_exception=True,
        )
        
        serializer.save()

        return Response(
            {
                "message": (
                    "Password reset successfully. "
                    "You can log in with your "
                    "new password."
                )
            },
            status=status.HTTP_200_OK,
        )