from django.urls import reverse

from rest_framework import status

from rest_framework_simplejwt.tokens import (
    RefreshToken,
)
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

from .base import UserAPITestCase


class LoginTests(UserAPITestCase):
    def setUp(self):
        super().setUp()

        self.user = self.create_user(
            username="shelly",
            email="shelly@example.com",
        )

        self.url = reverse(
            "users:login"
        )

    def test_login_with_username(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": "shelly",
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

        self.assertIn(
            "user",
            response.data,
        )

    def test_login_username_is_case_insensitive(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": "SHELLY",
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_login_with_email(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": (
                    "shelly@example.com"
                ),
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_login_email_is_case_insensitive(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": (
                    "SHELLY@EXAMPLE.COM"
                ),
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_login_wrong_password(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": "shelly",
                "password": "WrongPassword!123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_login_unknown_user(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "login": "unknown",
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_unactivated_user_cannot_login(
        self,
    ):
        user = self.create_user(
            username="inactive",
            email="inactive@example.com",
            active=False,
            verified=False,
        )

        response = self.client.post(
            self.url,
            {
                "login": user.username,
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertIn(
            "not been activated",
            str(response.data),
        )

    def test_disabled_verified_user_cannot_login(
        self,
    ):
        user = self.create_user(
            username="disabled",
            email="disabled@example.com",
            active=False,
            verified=True,
        )

        response = self.client.post(
            self.url,
            {
                "login": user.username,
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertIn(
            "disabled",
            str(response.data),
        )

    def test_login_updates_last_login(
        self,
    ):
        self.assertIsNone(
            self.user.last_login
        )

        response = self.client.post(
            self.url,
            {
                "login": self.user.username,
                "password": self.PASSWORD,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertIsNotNone(
            self.user.last_login
        )

    def test_access_token_can_authenticate(
        self,
    ):
        login_response = self.client.post(
            self.url,
            {
                "login": self.user.username,
                "password": self.PASSWORD,
            },
            format="json",
        )

        access = (
            login_response.data["access"]
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {access}"
            )
        )

        response = self.client.get(
            reverse("users:me")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )


class TokenTests(UserAPITestCase):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        refresh = RefreshToken.for_user(
            self.user
        )

        self.refresh_string = str(refresh)
        self.access_string = str(
            refresh.access_token
        )

    def test_refresh_token(
        self,
    ):
        response = self.client.post(
            reverse(
                "users:token-refresh"
            ),
            {
                "refresh": (
                    self.refresh_string
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertIn(
            "access",
            response.data,
        )

        self.assertIn(
            "refresh",
            response.data,
        )

    def test_refresh_rotation_blacklists_old_token(
        self,
    ):
        old_token = RefreshToken(
            self.refresh_string
        )

        old_jti = old_token["jti"]

        response = self.client.post(
            reverse(
                "users:token-refresh"
            ),
            {
                "refresh": (
                    self.refresh_string
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
                token__jti=old_jti
            ).exists()
        )

    def test_old_refresh_token_cannot_be_reused_after_rotation(
        self,
    ):
        url = reverse(
            "users:token-refresh"
        )

        first_response = (
            self.client.post(
                url,
                {
                    "refresh": (
                        self.refresh_string
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
                    "refresh": (
                        self.refresh_string
                    ),
                },
                format="json",
            )
        )

        self.assertEqual(
            second_response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_refresh_token(
        self,
    ):
        response = self.client.post(
            reverse(
                "users:token-refresh"
            ),
            {
                "refresh": (
                    "not-a-valid-token"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_verify_access_token(
        self,
    ):
        response = self.client.post(
            reverse(
                "users:token-verify"
            ),
            {
                "token": (
                    self.access_string
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_verify_invalid_token(
        self,
    ):
        response = self.client.post(
            reverse(
                "users:token-verify"
            ),
            {
                "token": "invalid",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class LogoutTests(UserAPITestCase):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        refresh = RefreshToken.for_user(
            self.user
        )

        self.refresh_string = str(refresh)
        self.refresh_jti = refresh["jti"]

        self.access = str(
            refresh.access_token
        )

        self.url = reverse(
            "users:logout"
        )

    def authenticate_with_access(
        self,
    ):
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {self.access}"
            )
        )

    def test_logout_requires_authentication(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "refresh": (
                    self.refresh_string
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_logout_blacklists_refresh_token(
        self,
    ):
        self.authenticate_with_access()

        response = self.client.post(
            self.url,
            {
                "refresh": (
                    self.refresh_string
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
                token__jti=self.refresh_jti
            ).exists()
        )

    def test_logged_out_refresh_token_cannot_be_used(
        self,
    ):
        self.authenticate_with_access()

        self.client.post(
            self.url,
            {
                "refresh": (
                    self.refresh_string
                ),
            },
            format="json",
        )

        self.client.credentials()

        response = self.client.post(
            reverse(
                "users:token-refresh"
            ),
            {
                "refresh": (
                    self.refresh_string
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_cannot_logout_using_another_users_refresh_token(
        self,
    ):
        other_user = self.create_user(
            username="other",
            email="other@example.com",
        )

        foreign_refresh = str(
            RefreshToken.for_user(
                other_user
            )
        )

        self.authenticate_with_access()

        response = self.client.post(
            self.url,
            {
                "refresh": (
                    foreign_refresh
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )