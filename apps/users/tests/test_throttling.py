from django.test import override_settings
from django.urls import reverse
from unittest.mock import patch

from django.urls import reverse

from rest_framework import status
from rest_framework.throttling import (
    ScopedRateThrottle,
)

from .base import UserAPITestCase

from rest_framework import status

from .base import UserAPITestCase


class ThrottleConfigurationTests(
    UserAPITestCase
):
    def test_required_throttle_scopes_exist(
        self,
    ):
        from django.conf import settings

        rates = settings.REST_FRAMEWORK[
            "DEFAULT_THROTTLE_RATES"
        ]

        expected_scopes = {
            "register",
            "login",
            "token_refresh",
            "resend_activation",
            "activation",
            "password_reset",
            "password_reset_confirm",
        }

        self.assertTrue(
            expected_scopes.issubset(
                rates.keys()
            )
        )


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": (
            (
                "rest_framework_simplejwt."
                "authentication."
                "JWTAuthentication"
            ),
        ),
        "DEFAULT_THROTTLE_RATES": {
            "login": "2/minute",
        },
    }
)


class LoginThrottleTests(
    UserAPITestCase
):
    @patch.object(
        ScopedRateThrottle,
        "THROTTLE_RATES",
        {
            "login": "2/minute",
        },
    )
    def test_login_is_rate_limited(
        self,
    ):
        url = reverse(
            "users:login"
        )

        payload = {
            "login": "nonexistent",
            "password": (
                "WrongPassword!123"
            ),
        }

        first = self.client.post(
            url,
            payload,
            format="json",
        )

        second = self.client.post(
            url,
            payload,
            format="json",
        )

        third = self.client.post(
            url,
            payload,
            format="json",
        )

        self.assertEqual(
            first.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(
            second.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

        self.assertEqual(
            third.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )