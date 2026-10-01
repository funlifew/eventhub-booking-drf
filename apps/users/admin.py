from django.contrib import admin
from django.contrib.auth.admin import (
    UserAdmin,
)

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_email_verified",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
    )

    ordering = (
        "-date_joined",
    )

    readonly_fields = (
        "last_login",
        "date_joined",
        "updated_at",
        "email_verified_at",
    )

    fieldsets = (
        *UserAdmin.fieldsets,
        (
            "EventHub profile",
            {
                "fields": (
                    "phone_number",
                    "bio",
                    "avatar",
                    "email_verified_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (
            "EventHub profile",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "phone_number",
                )
            },
        ),
    )