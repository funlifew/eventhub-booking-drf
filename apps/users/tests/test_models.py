from django.db import IntegrityError, transaction

from apps.users.models import User

from .base import UserAPITestCase


class UserModelTests(UserAPITestCase):
    def test_create_user_hashes_password(self):
        user = User.objects.create_user(
            username="shelly",
            email="shelly@example.com",
            password=self.PASSWORD,
        )

        self.assertNotEqual(
            user.password,
            self.PASSWORD,
        )

        self.assertTrue(
            user.check_password(
                self.PASSWORD
            )
        )

    def test_create_user_normalizes_email_to_lowercase(
        self,
    ):
        user = User.objects.create_user(
            username="shelly",
            email="Shelly@Example.COM",
            password=self.PASSWORD,
        )

        self.assertEqual(
            user.email,
            "shelly@example.com",
        )

    def test_email_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="shelly",
                email="",
                password=self.PASSWORD,
            )

    def test_username_is_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="",
                email="shelly@example.com",
                password=self.PASSWORD,
            )

    def test_username_is_case_insensitively_unique(
        self,
    ):
        self.create_user(
            username="shelly",
            email="one@example.com",
        )

        with self.assertRaises(
            IntegrityError
        ):
            with transaction.atomic():
                self.create_user(
                    username="SHELLY",
                    email="two@example.com",
                )

    def test_email_is_case_insensitively_unique(
        self,
    ):
        self.create_user(
            username="shelly",
            email="shelly@example.com",
        )

        with self.assertRaises(
            IntegrityError
        ):
            with transaction.atomic():
                self.create_user(
                    username="other",
                    email="SHELLY@EXAMPLE.COM",
                )

    def test_is_email_verified_false(
        self,
    ):
        user = self.create_user(
            active=False,
            verified=False,
        )

        self.assertFalse(
            user.is_email_verified
        )

    def test_is_email_verified_true(
        self,
    ):
        user = self.create_user()

        self.assertTrue(
            user.is_email_verified
        )

    def test_string_representation_is_username(
        self,
    ):
        user = self.create_user(
            username="shelly",
        )

        self.assertEqual(
            str(user),
            "shelly",
        )

    def test_create_superuser_sets_required_flags(
        self,
    ):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=self.PASSWORD,
        )

        self.assertTrue(
            user.is_staff
        )
        self.assertTrue(
            user.is_superuser
        )
        self.assertTrue(
            user.is_active
        )

    def test_superuser_email_is_verified(
        self,
    ):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password=self.PASSWORD,
        )

        self.assertIsNotNone(
            user.email_verified_at
        )

        self.assertTrue(
            user.is_email_verified
        )