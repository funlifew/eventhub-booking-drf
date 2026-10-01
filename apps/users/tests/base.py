from django.core.cache import cache
from django.utils import timezone

from rest_framework.test import APITestCase

from apps.users.models import User


class UserAPITestCase(APITestCase):
    PASSWORD = "EventHub!Secure#82941"
    NEW_PASSWORD = "EventHub!New#97421"

    def setUp(self):
        super().setUp()

        # DRF throttling uses Django's cache.
        # Clearing it prevents tests from affecting
        # each other's rate limits.
        cache.clear()

    def create_user(
        self,
        *,
        username="shelly",
        email="shelly@example.com",
        password=None,
        active=True,
        verified=True,
        **extra_fields,
    ):
        if password is None:
            password = self.PASSWORD

        email_verified_at = (
            timezone.now()
            if verified
            else None
        )

        return User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_active=active,
            email_verified_at=email_verified_at,
            **extra_fields,
        )

    def authenticate(self, user):
        self.client.force_authenticate(
            user=user,
        )