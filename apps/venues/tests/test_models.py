from django.db import (
    IntegrityError,
    transaction,
)

from .base import VenueAPITestCase


class VenueModelTests(
    VenueAPITestCase
):
    def test_default_country_is_iran(
        self,
    ):
        venue = self.create_venue(
            country="Iran",
        )

        self.assertEqual(
            venue.country,
            "Iran",
        )

    def test_default_city_is_tehran(
        self,
    ):
        venue = self.create_venue(
            city="Tehran",
        )

        self.assertEqual(
            venue.city,
            "Tehran",
        )

    def test_string_representation(
        self,
    ):
        venue = self.create_venue(
            name="Milad Hall",
            city="Tehran",
        )

        self.assertEqual(
            str(venue),
            "Milad Hall - Tehran",
        )

    def test_capacity_must_be_greater_than_zero(
        self,
    ):
        with self.assertRaises(
            IntegrityError
        ):
            with transaction.atomic():
                self.create_venue(
                    capacity=0,
                )

    def test_capacity_can_be_null(
        self,
    ):
        venue = self.create_venue(
            capacity=None,
        )

        self.assertIsNone(
            venue.capacity
        )

    def test_created_by_becomes_null_when_user_deleted(
        self,
    ):
        user = self.create_user()

        venue = self.create_venue(
            created_by=user
        )

        user.delete()

        venue.refresh_from_db()

        self.assertIsNone(
            venue.created_by
        )

    def test_venue_is_active_by_default(
        self,
    ):
        venue = self.create_venue()

        self.assertTrue(
            venue.is_active
        )