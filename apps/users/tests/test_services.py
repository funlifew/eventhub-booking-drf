from unittest.mock import patch

from django.test import RequestFactory
from django.urls import reverse

from rest_framework_simplejwt.tokens import (
    RefreshToken,
)
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from apps.users.services import (
    blacklist_all_refresh_tokens,
    build_activation_url,
    build_password_reset_url,
    send_activation_email,
    send_password_reset_email,
)

from .base import UserAPITestCase


class UserServiceTests(UserAPITestCase):
    def setUp(self):
        super().setUp()

        self.factory = RequestFactory()

        self.request = self.factory.get(
            "/"
        )

    def test_build_activation_url(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        url = build_activation_url(
            request=self.request,
            user=user,
        )

        self.assertTrue(
            url.startswith(
                "http://testserver/"
            )
        )

        self.assertIn(
            "/api/v1/users/activate/",
            url,
        )

    def test_build_password_reset_url(
        self,
    ):
        user = self.create_user()

        url = build_password_reset_url(
            request=self.request,
            user=user,
        )

        self.assertTrue(
            url.startswith(
                "http://testserver/"
            )
        )

        self.assertIn(
            (
                "/api/v1/users/"
                "password/reset/confirm/"
            ),
            url,
        )

    @patch(
        "apps.users.services.send_mail"
    )
    def test_send_activation_email(
        self,
        send_mail_mock,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        send_activation_email(
            request=self.request,
            user=user,
        )

        send_mail_mock.assert_called_once()

        kwargs = (
            send_mail_mock.call_args.kwargs
        )

        self.assertEqual(
            kwargs["subject"],
            "Activate your EventHub account",
        )

        self.assertEqual(
            kwargs["recipient_list"],
            [user.email],
        )

        self.assertEqual(
            kwargs["using"],
            "default",
        )

        self.assertIn(
            "/api/v1/users/activate/",
            kwargs["message"],
        )

    @patch(
        "apps.users.services.send_mail"
    )
    def test_send_password_reset_email(
        self,
        send_mail_mock,
    ):
        user = self.create_user()

        send_password_reset_email(
            request=self.request,
            user=user,
        )

        send_mail_mock.assert_called_once()

        kwargs = (
            send_mail_mock.call_args.kwargs
        )

        self.assertEqual(
            kwargs["subject"],
            "Reset your EventHub password",
        )

        self.assertEqual(
            kwargs["recipient_list"],
            [user.email],
        )

        self.assertIn(
            (
                "/api/v1/users/"
                "password/reset/confirm/"
            ),
            kwargs["message"],
        )

    def test_blacklist_all_refresh_tokens(
        self,
    ):
        user = self.create_user()

        RefreshToken.for_user(user)
        RefreshToken.for_user(user)

        self.assertEqual(
            OutstandingToken.objects.filter(
                user=user
            ).count(),
            2,
        )

        blacklist_all_refresh_tokens(
            user
        )

        self.assertEqual(
            BlacklistedToken.objects.filter(
                token__user=user
            ).count(),
            2,
        )