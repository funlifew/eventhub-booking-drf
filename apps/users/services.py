from django.conf import settings
from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from .tokens import account_activation_token

def build_activation_url(
    *,
    request,
    user,
):
    uidb64 = urlsafe_base64_encode(
        force_bytes(user.pk)
    )
    
    token = account_activation_token.make_token(
        user
    )
    
    path = reverse(
        "users:activate",
        kwargs={
            "uidb64": uidb64,
            "token": token,
        },
    )
    
    return request.build_absolute_uri(path)

def send_activation_email(
    *,
    request,
    user,
):
    activation_url = build_activation_url(
        request=request,
        user=user,
    )
    
    message = render_to_string(
        "users/emails/account_activation.txt",
        {
            "user": user,
            "activation_url": activation_url,
        },
    )
    
    send_mail(
        subject="Activate your EventHub account",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email,],
        using='default',
    )

def build_password_reset_url(
    *,
    request,
    user,
):
    uidb64 = urlsafe_base64_encode(
        force_bytes(user.pk)
    )
    
    token = default_token_generator.make_token(
        user
    )
    
    path = reverse(
        'users:password-reset-confirm',
        kwargs={
            'uidb64': uidb64,
            'token': token,
        },
    )
    
    return request.build_absolute_uri(path)

def send_password_reset_email(
    *,
    request,
    user,
):
    reset_url = build_password_reset_url(
        request=request,
        user=user,
    )
    
    message = render_to_string(
        'users/emails/password_reset.txt',
        {
            'user': user,
            'reset_url': reset_url,
        },
    )
    
    send_mail(
        subject="Reset your EventHub password",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        using="default",
    )


def blacklist_all_refresh_tokens(user):
    outstanding_tokens = (
        OutstandingToken.objects
        .filter(
            user=user
        )
    )
    
    for token in outstanding_tokens:
        BlacklistedToken.objects.get_or_create(
            token=token,
        )