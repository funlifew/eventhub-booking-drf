from datetime import datetime, timedelta
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import (
    urlsafe_base64_encode,
)

from apps.users.selectors import (
    get_user_by_email,
    get_user_by_login,
    get_user_from_uid,
)
from apps.users.tokens import (
    account_activation_token,
)

from .base import UserAPITestCase


class UserSelectorTests(UserAPITestCase):
    def test_get_user_by_username(
        self,
    ):
        user = self.create_user(
            username="shelly",
        )

        result = get_user_by_login(
            "shelly"
        )

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_by_username_is_case_insensitive(
        self,
    ):
        user = self.create_user(
            username="shelly",
        )

        result = get_user_by_login(
            "SHELLY"
        )

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_by_email(
        self,
    ):
        user = self.create_user(
            email="shelly@example.com",
        )

        result = get_user_by_login(
            "shelly@example.com"
        )

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_by_email_login_is_case_insensitive(
        self,
    ):
        user = self.create_user(
            email="shelly@example.com",
        )

        result = get_user_by_login(
            "SHELLY@EXAMPLE.COM"
        )

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_by_login_returns_none(
        self,
    ):
        result = get_user_by_login(
            "does-not-exist"
        )

        self.assertIsNone(result)

    def test_get_user_by_email_selector(
        self,
    ):
        user = self.create_user(
            email="shelly@example.com",
        )

        result = get_user_by_email(
            "SHELLY@EXAMPLE.COM"
        )

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_from_valid_uid(
        self,
    ):
        user = self.create_user()

        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        result = get_user_from_uid(uid)

        self.assertEqual(
            result,
            user,
        )

    def test_get_user_from_invalid_uid_returns_none(
        self,
    ):
        result = get_user_from_uid(
            "this-is-invalid"
        )

        self.assertIsNone(result)


class AccountActivationTokenTests(
    UserAPITestCase
):
    def test_activation_token_is_valid(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        token = (
            account_activation_token
            .make_token(user)
        )

        self.assertTrue(
            account_activation_token
            .check_token(
                user,
                token,
            )
        )

    def test_activation_token_becomes_invalid_after_activation(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        token = (
            account_activation_token
            .make_token(user)
        )

        user.is_active = True
        user.email_verified_at = (
            timezone.now()
        )

        user.save(
            update_fields=[
                "is_active",
                "email_verified_at",
            ]
        )

        self.assertFalse(
            account_activation_token
            .check_token(
                user,
                token,
            )
        )

    def test_activation_token_becomes_invalid_after_email_change(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        token = (
            account_activation_token
            .make_token(user)
        )

        user.email = (
            "new-email@example.com"
        )
        user.save(
            update_fields=["email"],
        )

        self.assertFalse(
            account_activation_token
            .check_token(
                user,
                token,
            )
        )

    def test_activation_token_becomes_invalid_after_password_change(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        token = (
            account_activation_token
            .make_token(user)
        )

        user.set_password(
            self.NEW_PASSWORD
        )

        user.save(
            update_fields=["password"],
        )

        self.assertFalse(
            account_activation_token
            .check_token(
                user,
                token,
            )
        )

    @override_settings(
        PASSWORD_RESET_TIMEOUT=60
    )
    def test_activation_token_expires(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        now = datetime.now()

        with patch.object(
            account_activation_token,
            "_now",
            return_value=now,
        ):
            token = (
                account_activation_token
                .make_token(user)
            )

        future = (
            now
            + timedelta(
                seconds=61,
            )
        )

        with patch.object(
            account_activation_token,
            "_now",
            return_value=future,
        ):
            is_valid = (
                account_activation_token
                .check_token(
                    user,
                    token,
                )
            )

        self.assertFalse(is_valid)