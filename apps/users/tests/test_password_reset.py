from unittest.mock import patch

from django.contrib.auth.tokens import (
    default_token_generator,
)
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import (
    urlsafe_base64_encode,
)

from rest_framework import status
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

from .base import UserAPITestCase


class PasswordResetRequestTests(
    UserAPITestCase
):
    def setUp(self):
        super().setUp()

        self.url = reverse(
            "users:password-reset"
        )

    @patch(
        "apps.users.views.send_password_reset_email"
    )
    def test_active_user_receives_reset_email(
        self,
        send_email_mock,
    ):
        user = self.create_user()

        response = self.client.post(
            self.url,
            {
                "email": user.email,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        send_email_mock.assert_called_once()

    @patch(
        "apps.users.views.send_password_reset_email"
    )
    def test_unknown_email_does_not_reveal_account_existence(
        self,
        send_email_mock,
    ):
        response = self.client.post(
            self.url,
            {
                "email": (
                    "unknown@example.com"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        send_email_mock.assert_not_called()

    @patch(
        "apps.users.views.send_password_reset_email"
    )
    def test_inactive_user_does_not_receive_reset_email(
        self,
        send_email_mock,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        response = self.client.post(
            self.url,
            {
                "email": user.email,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        send_email_mock.assert_not_called()

    def test_invalid_email_format(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "email": "not-an-email",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class PasswordResetConfirmTests(
    UserAPITestCase
):
    def get_reset_url(
        self,
        user,
        token=None,
    ):
        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        if token is None:
            token = (
                default_token_generator
                .make_token(user)
            )

        return reverse(
            "users:password-reset-confirm",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )

    def test_reset_password_success(
        self,
    ):
        user = self.create_user()

        response = self.client.post(
            self.get_reset_url(user),
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    self.NEW_PASSWORD
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.check_password(
                self.NEW_PASSWORD
            )
        )

        self.assertFalse(
            user.check_password(
                self.PASSWORD
            )
        )

    def test_reset_password_blacklists_existing_refresh_tokens(
        self,
    ):
        user = self.create_user()

        refresh = RefreshToken.for_user(
            user
        )

        refresh_jti = refresh["jti"]

        response = self.client.post(
            self.get_reset_url(user),
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    self.NEW_PASSWORD
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__jti=refresh_jti
            ).exists()
        )

    def test_reset_token_cannot_be_reused(
        self,
    ):
        user = self.create_user()

        url = self.get_reset_url(
            user
        )

        first_response = (
            self.client.post(
                url,
                {
                    "new_password": (
                        self.NEW_PASSWORD
                    ),
                    "new_password_confirm": (
                        self.NEW_PASSWORD
                    ),
                },
                format="json",
            )
        )

        self.assertEqual(
            first_response.status_code,
            status.HTTP_200_OK,
        )

        second_response = (
            self.client.post(
                url,
                {
                    "new_password": (
                        "Another!Password9123"
                    ),
                    "new_password_confirm": (
                        "Another!Password9123"
                    ),
                },
                format="json",
            )
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_reset_token(
        self,
    ):
        user = self.create_user()

        response = self.client.post(
            self.get_reset_url(
                user,
                token="invalid-token",
            ),
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    self.NEW_PASSWORD
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_uid(
        self,
    ):
        url = reverse(
            "users:password-reset-confirm",
            kwargs={
                "uidb64": "invalid",
                "token": "invalid",
            },
        )

        response = self.client.post(
            url,
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    self.NEW_PASSWORD
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_inactive_user_cannot_reset_password(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        response = self.client.post(
            self.get_reset_url(user),
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    self.NEW_PASSWORD
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_password_confirmation_must_match(
        self,
    ):
        user = self.create_user()

        response = self.client.post(
            self.get_reset_url(user),
            {
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    "Different!123456"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password_confirm",
            response.data,
        )

    def test_new_password_must_pass_django_validators(
        self,
    ):
        user = self.create_user()

        response = self.client.post(
            self.get_reset_url(user),
            {
                "new_password": "password",
                "new_password_confirm": (
                    "password"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "new_password",
            response.data,
        )