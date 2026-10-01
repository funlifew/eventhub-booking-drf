from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path(
        "register/",
        views.RegisterView.as_view(),
        name="register",
    ),
    path(
        'activate/<uidb64>/<token>/',
        views.ActivateAccountView.as_view(),
        name="activate",
    ),
    path(
        "activate/resend/",
        views.ResendActivationView.as_view(),
        name="resend-activation",
    ),
    path(
        "login/",
        views.LoginView.as_view(),
        name="login",
    ),
    path(
        "token/refresh/",
        views.RefreshTokenView.as_view(),
        name='token-refresh',
    ),
    path(
        "token/verify/",
        views.VerifyTokenView.as_view(),
        name="token-verify",
    ),
    path(
        "logout/",
        views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "me/",
        views.MeView.as_view(),
        name="me",
    ),
    path(
        "password/change/",
        views.ChangePasswordView.as_view(),
        name="password-change",
    ),
    path(
        "password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset",
    ),
    path(
        "password/reset/confirm/<uidb64>/<token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
