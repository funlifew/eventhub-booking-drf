from unittest.mock import patch

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import (
    urlsafe_base64_encode,
)

from rest_framework import status

from apps.users.models import User
from apps.users.tokens import (
    account_activation_token,
)

from .base import UserAPITestCase


class RegistrationTests(
    UserAPITestCase
):
    def setUp(self):
        super().setUp()

        self.url = reverse(
            "users:register"
        )

        self.payload = {
            "username": "shelly",
            "email": "shelly@example.com",
            "first_name": "Shelly",
            "last_name": "Moon",
            "password": self.PASSWORD,
            "password_confirm": (
                self.PASSWORD
            ),
        }

    @patch(
        "apps.users.views.send_activation_email"
    )
    def test_register_success(
        self,
        send_email_mock,
    ):
        with self.captureOnCommitCallbacks(
            execute=True
        ):
            response = self.client.post(
                self.url,
                self.payload,
                format="json",
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            User.objects.count(),
            1,
        )

        user = User.objects.get()

        self.assertFalse(
            user.is_active
        )

        self.assertFalse(
            user.is_email_verified
        )

        self.assertTrue(
            user.check_password(
                self.PASSWORD
            )
        )

        send_email_mock.assert_called_once()

    def test_register_normalizes_email(
        self,
    ):
        payload = {
            **self.payload,
            "email": "SHELLY@EXAMPLE.COM",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        user = User.objects.get()

        self.assertEqual(
            user.email,
            "shelly@example.com",
        )

    def test_register_duplicate_username(
        self,
    ):
        self.create_user(
            username="shelly",
            email="old@example.com",
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "username",
            response.data,
        )

    def test_register_duplicate_username_case_insensitive(
        self,
    ):
        self.create_user(
            username="SHELLY",
            email="old@example.com",
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_register_duplicate_email_case_insensitive(
        self,
    ):
        self.create_user(
            username="old-user",
            email="SHELLY@EXAMPLE.COM",
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "email",
            response.data,
        )

    def test_register_password_mismatch(
        self,
    ):
        payload = {
            **self.payload,
            "password_confirm": (
                "DifferentPassword!983"
            ),
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "password_confirm",
            response.data,
        )

    def test_register_weak_password(
        self,
    ):
        payload = {
            **self.payload,
            "password": "password",
            "password_confirm": "password",
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertIn(
            "password",
            response.data,
        )


class AccountActivationTests(
    UserAPITestCase
):
    def get_activation_url(
        self,
        user,
        token=None,
    ):
        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        if token is None:
            token = (
                account_activation_token
                .make_token(user)
            )

        return reverse(
            "users:activate",
            kwargs={
                "uidb64": uid,
                "token": token,
            },
        )

    def test_activate_account_success(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        response = self.client.get(
            self.get_activation_url(
                user
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        user.refresh_from_db()

        self.assertTrue(
            user.is_active
        )

        self.assertIsNotNone(
            user.email_verified_at
        )

    def test_activation_with_invalid_token(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        response = self.client.get(
            self.get_activation_url(
                user,
                token="invalid-token",
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertFalse(
            user.is_active
        )

    def test_activation_with_invalid_uid(
        self,
    ):
        response = self.client.get(
            reverse(
                "users:activate",
                kwargs={
                    "uidb64": "invalid",
                    "token": "invalid",
                },
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_activation_of_already_active_account(
        self,
    ):
        user = self.create_user()

        response = self.client.get(
            self.get_activation_url(
                user
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["message"],
            "Account is already active.",
        )

    def test_verified_but_disabled_user_cannot_reactivate(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=True,
        )

        response = self.client.get(
            self.get_activation_url(
                user
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        user.refresh_from_db()

        self.assertFalse(
            user.is_active
        )


class ResendActivationTests(
    UserAPITestCase
):
    def setUp(self):
        super().setUp()

        self.url = reverse(
            "users:resend-activation"
        )

    @patch(
        "apps.users.views.send_activation_email"
    )
    def test_resend_for_inactive_unverified_user(
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

        send_email_mock.assert_called_once()

    @patch(
        "apps.users.views.send_activation_email"
    )
    def test_resend_does_not_reveal_unknown_email(
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
        "apps.users.views.send_activation_email"
    )
    def test_resend_does_not_send_for_active_user(
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

        send_email_mock.assert_not_called()

    @patch(
        "apps.users.views.send_activation_email"
    )
    def test_resend_does_not_reactivate_disabled_verified_user(
        self,
        send_email_mock,
    ):
        user = self.create_user(
            active=False,
            verified=True,
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