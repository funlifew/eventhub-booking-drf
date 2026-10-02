from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework import status

from apps.events.models import Event
from apps.venues.models import Venue

from .base import VenueAPITestCase


class VenueListTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user(
            username="shelly",
            email="shelly@example.com",
        )

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.active = self.create_venue(
            created_by=self.owner,
            name="Active Venue",
        )

        self.inactive = (
            self.create_venue(
                created_by=self.owner,
                name="Inactive Venue",
                is_active=False,
            )
        )

        self.other_inactive = (
            self.create_venue(
                created_by=self.other,
                name="Other Inactive",
                is_active=False,
            )
        )

        self.url = reverse(
            "venues:venue-list"
        )

    def test_public_list_only_shows_active_venues(
        self,
    ):
        response = self.client.get(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ids = {
            item["id"]
            for item
            in response.data["results"]
        }

        self.assertIn(
            self.active.id,
            ids,
        )

        self.assertNotIn(
            self.inactive.id,
            ids,
        )

        self.assertNotIn(
            self.other_inactive.id,
            ids,
        )

    def test_authenticated_default_list_only_shows_active(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.get(
            self.url
        )

        ids = {
            item["id"]
            for item
            in response.data["results"]
        }

        self.assertIn(
            self.active.id,
            ids,
        )

        self.assertNotIn(
            self.inactive.id,
            ids,
        )

    def test_mine_returns_active_and_inactive_owned_venues(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.get(
            self.url,
            {
                "mine": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        ids = {
            item["id"]
            for item
            in response.data["results"]
        }

        self.assertIn(
            self.active.id,
            ids,
        )

        self.assertIn(
            self.inactive.id,
            ids,
        )

        self.assertNotIn(
            self.other_inactive.id,
            ids,
        )

    def test_mine_requires_authentication(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "mine": "true",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_mine_parameter(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "mine": "banana",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )


class VenueCreateTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.url = reverse(
            "venues:venue-list"
        )

        self.payload = {
            "name": "Azadi Hall",
            "country": "Iran",
            "city": "Tehran",
            "address": (
                "Azadi Square, Tehran"
            ),
            "capacity": 2500,
        }

    def test_authenticated_user_can_create_venue(
        self,
    ):
        self.authenticate(
            self.user
        )

        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        venue = Venue.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            venue.created_by,
            self.user,
        )

        self.assertTrue(
            venue.is_active
        )

    def test_anonymous_user_cannot_create(
        self,
    ):
        response = self.client.post(
            self.url,
            self.payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_created_by_cannot_be_spoofed(
        self,
    ):
        self.authenticate(
            self.user
        )

        payload = {
            **self.payload,
            "created_by": (
                self.other.id
            ),
        }

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        venue = Venue.objects.get(
            id=response.data["id"]
        )

        self.assertEqual(
            venue.created_by,
            self.user,
        )

    def test_capacity_zero_is_invalid(
        self,
    ):
        self.authenticate(
            self.user
        )

        payload = {
            **self.payload,
            "capacity": 0,
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
            "capacity",
            response.data,
        )

    def test_capacity_can_be_null(
        self,
    ):
        self.authenticate(
            self.user
        )

        payload = {
            **self.payload,
            "capacity": None,
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


class VenueDetailTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user()

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.active = self.create_venue(
            created_by=self.owner,
        )

        self.inactive = (
            self.create_venue(
                created_by=self.owner,
                name="Inactive",
                is_active=False,
            )
        )

    def test_public_can_retrieve_active_venue(
        self,
    ):
        response = self.client.get(
            reverse(
                "venues:venue-detail",
                args=[self.active.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_public_cannot_retrieve_inactive_venue(
        self,
    ):
        response = self.client.get(
            reverse(
                "venues:venue-detail",
                args=[self.inactive.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_owner_can_retrieve_own_inactive_venue(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.get(
            reverse(
                "venues:venue-detail",
                args=[self.inactive.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_events_count_is_returned(
        self,
    ):
        now = timezone.now()

        Event.objects.create(
            title="Django Conference",
            description="DRF event",
            organizer=self.active,
            start_at=(
                now
                + timedelta(days=1)
            ),
            end_at=(
                now
                + timedelta(days=2)
            ),
        )

        response = self.client.get(
            reverse(
                "venues:venue-detail",
                args=[self.active.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data[
                "events_count"
            ],
            1,
        )


class VenueUpdateTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user()

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.venue = self.create_venue(
            created_by=self.owner,
        )

        self.url = reverse(
            "venues:venue-detail",
            args=[self.venue.id],
        )

    def test_owner_can_update_venue(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.patch(
            self.url,
            {
                "name": (
                    "Updated Venue"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.venue.refresh_from_db()

        self.assertEqual(
            self.venue.name,
            "Updated Venue",
        )

    def test_non_owner_cannot_update(
        self,
    ):
        self.authenticate(
            self.other
        )

        response = self.client.patch(
            self.url,
            {
                "name": "Hacked",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_cannot_update(
        self,
    ):
        response = self.client.patch(
            self.url,
            {
                "name": "Hacked",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_is_active_cannot_be_changed_via_patch(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.patch(
            self.url,
            {
                "is_active": False,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.venue.refresh_from_db()

        self.assertTrue(
            self.venue.is_active
        )


class VenueDeleteTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user()

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.venue = self.create_venue(
            created_by=self.owner,
        )

        self.url = reverse(
            "venues:venue-detail",
            args=[self.venue.id],
        )

    def test_delete_soft_deletes_venue(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.venue.refresh_from_db()

        self.assertFalse(
            self.venue.is_active
        )

        self.assertTrue(
            Venue.objects.filter(
                id=self.venue.id
            ).exists()
        )

    def test_non_owner_cannot_delete(
        self,
    ):
        self.authenticate(
            self.other
        )

        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_cannot_delete(
        self,
    ):
        response = self.client.delete(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class VenueActivationTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user()

        self.other = self.create_user(
            username="other",
            email="other@example.com",
        )

        self.venue = self.create_venue(
            created_by=self.owner,
            is_active=False,
        )

        self.url = reverse(
            "venues:venue-activate",
            args=[self.venue.id],
        )

    def test_owner_can_activate_venue(
        self,
    ):
        self.authenticate(
            self.owner
        )

        response = self.client.post(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.venue.refresh_from_db()

        self.assertTrue(
            self.venue.is_active
        )

    def test_other_user_cannot_discover_or_activate_inactive_venue(
        self,
    ):
        self.authenticate(
            self.other
        )

        response = self.client.post(
            self.url
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class VenueFilteringTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.user = self.create_user()

        self.tehran = self.create_venue(
            created_by=self.user,
            name="Tehran Hall",
            city="Tehran",
            country="Iran",
            capacity=1000,
        )

        self.shiraz = self.create_venue(
            created_by=self.user,
            name="Shiraz Arena",
            city="Shiraz",
            country="Iran",
            capacity=5000,
        )

        self.istanbul = self.create_venue(
            created_by=self.user,
            name="Istanbul Center",
            city="Istanbul",
            country="Turkey",
            capacity=2500,
        )

        self.url = reverse(
            "venues:venue-list"
        )

    def ids_from_response(
        self,
        response,
    ):
        return {
            item["id"]
            for item
            in response.data["results"]
        }

    def test_filter_by_city_is_case_insensitive(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "city": "tehran",
            },
        )

        ids = self.ids_from_response(
            response
        )

        self.assertEqual(
            ids,
            {self.tehran.id},
        )

    def test_filter_by_country(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "country": "Turkey",
            },
        )

        ids = self.ids_from_response(
            response
        )

        self.assertEqual(
            ids,
            {self.istanbul.id},
        )

    def test_filter_by_min_capacity(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "min_capacity": 2000,
            },
        )

        ids = self.ids_from_response(
            response
        )

        self.assertEqual(
            ids,
            {
                self.shiraz.id,
                self.istanbul.id,
            },
        )

    def test_filter_by_max_capacity(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "max_capacity": 2000,
            },
        )

        ids = self.ids_from_response(
            response
        )

        self.assertEqual(
            ids,
            {
                self.tehran.id,
            },
        )

    def test_invalid_capacity_filter_returns_400(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "min_capacity": "banana",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_search_by_name(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "search": "Shiraz",
            },
        )

        ids = self.ids_from_response(
            response
        )

        self.assertEqual(
            ids,
            {self.shiraz.id},
        )

    def test_order_by_capacity(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "ordering": "capacity",
            },
        )

        capacities = [
            item["capacity"]
            for item
            in response.data["results"]
        ]

        self.assertEqual(
            capacities,
            sorted(capacities),
        )

    def test_reverse_order_by_capacity(
        self,
    ):
        response = self.client.get(
            self.url,
            {
                "ordering": "-capacity",
            },
        )

        capacities = [
            item["capacity"]
            for item
            in response.data["results"]
        ]

        self.assertEqual(
            capacities,
            sorted(
                capacities,
                reverse=True,
            ),
        )


class VenuePaginationTests(
    VenueAPITestCase
):
    def test_page_size_parameter(
        self,
    ):
        user = self.create_user()

        for index in range(5):
            self.create_venue(
                created_by=user,
                name=f"Venue {index}",
            )

        response = self.client.get(
            reverse(
                "venues:venue-list"
            ),
            {
                "page_size": 2,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["count"],
            5,
        )

        self.assertEqual(
            len(
                response.data["results"]
            ),
            2,
        )


class VenueAdminPermissionTests(
    VenueAPITestCase
):
    def setUp(self):
        super().setUp()

        self.owner = self.create_user()

        self.admin = self.create_user(
            username="admin",
            email="admin@example.com",
            is_staff=True,
        )

        self.inactive = self.create_venue(
            created_by=self.owner,
            is_active=False,
        )

    def test_staff_can_see_inactive_venues(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.get(
            reverse(
                "venues:venue-list"
            )
        )

        ids = {
            item["id"]
            for item
            in response.data["results"]
        }

        self.assertIn(
            self.inactive.id,
            ids,
        )

    def test_staff_can_update_other_users_venue(
        self,
    ):
        self.authenticate(
            self.admin
        )

        response = self.client.patch(
            reverse(
                "venues:venue-detail",
                args=[
                    self.inactive.id
                ],
            ),
            {
                "name": (
                    "Admin Updated"
                ),
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )