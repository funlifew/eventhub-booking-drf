from django.utils.dateparse import (
    parse_datetime,
)

from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.filters import (
    BaseFilterBackend,
)

from .models import Event


class EventFilterBackend(
    BaseFilterBackend
):
    TRUE_VALUES = {
        "true",
        "1",
        "yes",
    }

    FALSE_VALUES = {
        "false",
        "0",
        "no",
    }

    def filter_queryset(
        self,
        request,
        queryset,
        view,
    ):
        category = (
            request.query_params.get(
                "category"
            )
        )

        status_value = (
            request.query_params.get(
                "status"
            )
        )

        venue = (
            request.query_params.get(
                "venue"
            )
        )

        city = (
            request.query_params.get(
                "city"
            )
        )

        featured = (
            request.query_params.get(
                "featured"
            )
        )

        upcoming = (
            request.query_params.get(
                "upcoming"
            )
        )

        start_from = (
            request.query_params.get(
                "start_from"
            )
        )

        start_to = (
            request.query_params.get(
                "start_to"
            )
        )

        if category:
            valid_categories = {
                choice
                for choice, _
                in Event.Category.choices
            }

            if category not in valid_categories:
                raise ValidationError(
                    {
                        "category": (
                            "Invalid event "
                            "category."
                        )
                    }
                )

            queryset = queryset.filter(
                category=category
            )

        if status_value:
            valid_statuses = {
                choice
                for choice, _
                in Event.Status.choices
            }

            if (
                status_value
                not in valid_statuses
            ):
                raise ValidationError(
                    {
                        "status": (
                            "Invalid event "
                            "status."
                        )
                    }
                )

            queryset = queryset.filter(
                status=status_value
            )

        if venue:
            try:
                venue_id = int(venue)

            except ValueError as exc:
                raise ValidationError(
                    {
                        "venue": (
                            "Venue must be "
                            "an integer ID."
                        )
                    }
                ) from exc

            queryset = queryset.filter(
                venue_id=venue_id
            )

        if city:
            queryset = queryset.filter(
                venue__city__iexact=(
                    city.strip()
                )
            )

        if featured is not None:
            queryset = queryset.filter(
                is_featured=(
                    self._parse_bool(
                        featured,
                        "featured",
                    )
                )
            )

        if upcoming is not None:
            is_upcoming = (
                self._parse_bool(
                    upcoming,
                    "upcoming",
                )
            )

            from django.utils import timezone

            if is_upcoming:
                queryset = queryset.filter(
                    start_at__gte=(
                        timezone.now()
                    )
                )

            else:
                queryset = queryset.filter(
                    start_at__lt=(
                        timezone.now()
                    )
                )

        if start_from:
            parsed = (
                parse_datetime(start_from)
            )

            if parsed is None:
                raise ValidationError(
                    {
                        "start_from": (
                            "Invalid datetime."
                        )
                    }
                )

            queryset = queryset.filter(
                start_at__gte=parsed
            )

        if start_to:
            parsed = (
                parse_datetime(start_to)
            )

            if parsed is None:
                raise ValidationError(
                    {
                        "start_to": (
                            "Invalid datetime."
                        )
                    }
                )

            queryset = queryset.filter(
                start_at__lte=parsed
            )

        return queryset

    def _parse_bool(
        self,
        value,
        field,
    ):
        value = (
            str(value)
            .strip()
            .lower()
        )

        if value in self.TRUE_VALUES:
            return True

        if value in self.FALSE_VALUES:
            return False

        raise ValidationError(
            {
                field: (
                    "Must be one of: "
                    "true, false, 1, 0, "
                    "yes, no."
                )
            }
        )