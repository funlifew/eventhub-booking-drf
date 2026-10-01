from django.urls import reverse

from rest_framework import status
from rest_framework_simplejwt.tokens import (
    RefreshToken,
)
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
)

from .base import UserAPITestCase


class ProfileTests(UserAPITestCase):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        self.url = reverse(
            "users:me"
        )

    def test_me_requires_authentication(
        self,
    ):
        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_get_current_user(
        self,
    ):
        self.authenticate(
            self.user
        )

        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            self.user.username,
        )

        self.assertEqual(
            response.data["email"],
            self.user.email,
        )

        self.assertTrue(
            response.data[
                "is_email_verified"
            ]
        )

    def test_update_profile(
        self,
    ):
        self.authenticate(
            self.user
        )

        response = self.client.patch(
            self.url,
            {
                "first_name": "Shelly",
                "last_name": "Moon",
                "bio": (
                    "EventHub test user"
                ),
                "phone_number": (
                    "09123456789"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Shelly",
        )

        self.assertEqual(
            self.user.bio,
            "EventHub test user",
        )

    def test_email_cannot_be_changed_from_me_endpoint(
        self,
    ):
        old_email = self.user.email

        self.authenticate(
            self.user
        )

        response = self.client.patch(
            self.url,
            {
                "email": (
                    "changed@example.com"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.email,
            old_email,
        )

    def test_username_can_be_changed(
        self,
    ):
        self.authenticate(
            self.user
        )

        response = self.client.patch(
            self.url,
            {
                "username": "new-shelly",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.username,
            "new-shelly",
        )

    def test_duplicate_username_is_rejected(
        self,
    ):
        self.create_user(
            username="taken",
            email="taken@example.com",
        )

        self.authenticate(
            self.user
        )

        response = self.client.patch(
            self.url,
            {
                "username": "TAKEN",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class ChangePasswordTests(
    UserAPITestCase
):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        self.refresh = (
            RefreshToken.for_user(
                self.user
            )
        )

        self.refresh_jti = (
            self.refresh["jti"]
        )

        self.access = str(
            self.refresh.access_token
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {self.access}"
            )
        )

        self.url = reverse(
            "users:password-change"
        )

    def test_change_password_success(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
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

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password(
                self.NEW_PASSWORD
            )
        )

        self.assertFalse(
            self.user.check_password(
                self.PASSWORD
            )
        )

    def test_change_password_blacklists_refresh_tokens(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
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
                token__jti=(
                    self.refresh_jti
                )
            ).exists()
        )

    def test_old_access_token_is_invalid_after_password_change(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
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

        # Still using the old access token.
        response = self.client.get(
            reverse("users:me")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_wrong_old_password(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    "WrongPassword!123"
                ),
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

        self.assertIn(
            "old_password",
            response.data,
        )

    def test_new_password_mismatch(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
                "new_password": (
                    self.NEW_PASSWORD
                ),
                "new_password_confirm": (
                    "Different!Password123"
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

    def test_weak_new_password(
        self,
    ):
        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
                "new_password": (
                    "password"
                ),
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

    def test_change_password_requires_authentication(
        self,
    ):
        self.client.credentials()

        response = self.client.post(
            self.url,
            {
                "old_password": (
                    self.PASSWORD
                ),
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
            status.HTTP_401_UNAUTHORIZED,
        )