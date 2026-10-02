from django.contrib import admin

from .models import Venue


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "city",
        "country",
        "capacity",
        "created_by",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "country",
        "city",
    )

    search_fields = (
        "name",
        "address",
        "city",
        "country",
        "created_by__username",
        "created_by__email",
    )

    ordering = (
        "-created_at",
    )

    list_select_related = (
        "created_by",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )