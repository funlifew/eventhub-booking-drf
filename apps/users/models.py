from django.contrib.auth.models import (
    AbstractUser,
    UserManager as DjangoUserManager,
)
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone


class UserManager(DjangoUserManager):
    def _create_user(
        self,
        username,
        email,
        password,
        **extra_fields,
    ):
        if not username:
            raise ValueError("Username is required.")
        
        if not email:
            raise ValueError("Email is required.")
        
        email = self.normalize_email(email).strip().lower()

        return super()._create_user(
            username=username,
            email=email,
            password=password,
            **extra_fields,

        )
    
    def create_superuser(
        self,
        username,
        email=None,
        password=None,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "email_verified_at",
            timezone.now(),
        )
        
        return super().create_superuser(
            username=username,
            email=email,
            password=password,
            **extra_fields,
        )

class User(AbstractUser):
    email = models.EmailField(
        unique=True,
    )

    phone_number = models.CharField(
        max_length=32,
        blank=True,
    )

    bio = models.TextField(
        blank=True,
    )

    avatar = models.ImageField(
        upload_to="users/avatars/",
        blank=True,
        null=True,
    )
    
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    objects = UserManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="users_email_case_insensitive_unique",
            ),
            models.UniqueConstraint(
                Lower("username"),
                name="users_username_case_insensitive_unique",
            ),
        ]
    
    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    def __str__(self):
        return self.username