from django.utils import timezone

from rest_framework.test import (
    APITestCase,
)

from apps.users.models import User
from apps.venues.models import Venue


class VenueAPITestCase(
    APITestCase
):
    PASSWORD = (
        "EventHub!Venue#82941"
    )

    def create_user(
        self,
        *,
        username="shelly",
        email="shelly@example.com",
        is_staff=False,
        is_superuser=False,
    ):
        return User.objects.create_user(
            username=username,
            email=email,
            password=self.PASSWORD,
            is_active=True,
            email_verified_at=(
                timezone.now()
            ),
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    def create_venue(
        self,
        *,
        created_by=None,
        name="Milad Hall",
        country="Iran",
        city="Tehran",
        address="Tehran, Iran",
        capacity=1000,
        is_active=True,
    ):
        return Venue.objects.create(
            name=name,
            country=country,
            city=city,
            address=address,
            capacity=capacity,
            created_by=created_by,
            is_active=is_active,
        )

    def authenticate(
        self,
        user,
    ):
        self.client.force_authenticate(
            user=user
        )