from django.db.models import Sum
from django.utils import timezone

from rest_framework import serializers

from .models import Event, TicketType

class EventSerializer(
    serializers.ModelSerializer
):
    venue_name = serializers.CharField(
        source='venue.name',
        read_only=True,
    )
    
    venue_city = serializers.CharField(
        source='venue.city',
        read_only=True,
    )
    
    ticket_types_count = (
        serializers.IntegerField(
            read_only=True,
            default=0
        )
    )
    
    total_tickets_capacity = (
        serializers.IntegerField(
            read_only=True,
            default=0,
        )
    )
    
    
    class Meta:
        model = Event
        
        fields = (
            "id",
            "title",
            "description",
            "venue",
            "venue_name",
            "venue_city",
            "category",
            "status",
            "start_at",
            "end_at",
            "banner",
            "is_featured",
            "ticket_types_count",
            "total_ticket_capacity",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "status",
            "is_featured",
            "ticket_types_count",
            "total_ticket_capacity",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        instance = self.instance
        
        venue = attrs.get(
            'venue',
            (
                instance.venue
                if instance
                else None
            ),
        )
        
        start_at = attrs.get(
            "start_at",
            (
                instance.start_at
                if instance
                else None
            ),
        )

        end_at = attrs.get(
            "end_at",
            (
                instance.end_at
                if instance
                else None
            ),
        )

        if (
            start_at
            and end_at
            and end_at <= start_at
        ):
            raise serializers.ValidationError(
                {
                    "end_at": (
                        "Event end time must "
                        "be after start time."
                    )
                }
            )

        if venue and not venue.is_active:
            raise serializers.ValidationError(
                {
                    "venue": (
                        "Events cannot use an "
                        "inactive venue."
                    )
                }
            )

        if instance is None:
            if (
                start_at
                and start_at
                <= timezone.now()
            ):
                raise serializers.ValidationError(
                    {
                        "start_at": (
                            "Event start time "
                            "must be in the future."
                        )
                    }
                )

            return attrs

        if (
            instance.status
            in {
                Event.Status.CANCELLED,
                Event.Status.COMPLETED,
            }
            and attrs
        ):
            raise serializers.ValidationError(
                (
                    "Cancelled or completed "
                    "events cannot be edited."
                )
            )

        if (
            instance.status
            == Event.Status.PUBLISHED
        ):
            protected_fields = {
                "venue",
                "category",
                "start_at",
                "end_at",
            }

            changed_fields = []

            for field in protected_fields:
                if field not in attrs:
                    continue

                old_value = getattr(
                    instance,
                    field,
                )

                if attrs[field] != old_value:
                    changed_fields.append(
                        field
                    )

            if changed_fields:
                raise serializers.ValidationError(
                    {
                        "detail": (
                            "These fields cannot "
                            "be changed after "
                            "publishing: "
                            + ", ".join(
                                sorted(
                                    changed_fields
                                )
                            )
                        )
                    }
                )

        if (
            "venue" in attrs
            and instance.ticket_types.exists()
            and venue.capacity is not None
        ):
            total_capacity = (
                instance.ticket_types.aggregate(
                    total=Sum("capacity")
                )["total"]
                or 0
            )

            if (
                total_capacity
                > venue.capacity
            ):
                raise serializers.ValidationError(
                    {
                        "venue": (
                            "This venue is too "
                            "small for the existing "
                            "ticket capacity."
                        )
                    }
                )

        return attrs

class TicketTypeSerializer(
    serializers.ModelSerializer
):
    event = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    class Meta:
        model = TicketType

        fields = (
            "id",
            "event",
            "name",
            "price",
            "capacity",
            "max_per_booking",
            "sales_start_at",
            "sales_end_at",
            "is_active",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "event",
            "created_at",
            "updated_at",
        )

    def validate_name(
        self,
        value,
    ):
        value = value.strip()

        event = self.context.get(
            "event"
        )

        if event is None:
            return value

        queryset = (
            TicketType.objects.filter(
                event=event,
                name__iexact=value,
            )
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                (
                    "A ticket type with this "
                    "name already exists for "
                    "this event."
                )
            )

        return value

    def validate(self, attrs):
        event = self.context.get(
            "event"
        )

        if event is None:
            raise serializers.ValidationError(
                {
                    "event": (
                        "Event context "
                        "is required."
                    )
                }
            )

        if (
            event.status
            != Event.Status.DRAFT
        ):
            raise serializers.ValidationError(
                {
                    "event": (
                        "Ticket types can only "
                        "be modified while the "
                        "event is a draft."
                    )
                }
            )

        capacity = attrs.get(
            "capacity",
            (
                self.instance.capacity
                if self.instance
                else None
            ),
        )

        max_per_booking = attrs.get(
            "max_per_booking",
            (
                self.instance.max_per_booking
                if self.instance
                else 5
            ),
        )

        if (
            capacity is not None
            and max_per_booking
            > capacity
        ):
            raise serializers.ValidationError(
                {
                    "max_per_booking": (
                        "Maximum tickets per "
                        "booking cannot exceed "
                        "ticket capacity."
                    )
                }
            )

        sales_start_at = attrs.get(
            "sales_start_at",
            (
                self.instance.sales_start_at
                if self.instance
                else None
            ),
        )

        sales_end_at = attrs.get(
            "sales_end_at",
            (
                self.instance.sales_end_at
                if self.instance
                else None
            ),
        )

        if (
            sales_start_at
            and sales_end_at
            and sales_end_at
            <= sales_start_at
        ):
            raise serializers.ValidationError(
                {
                    "sales_end_at": (
                        "Sales end time must "
                        "be after sales start "
                        "time."
                    )
                }
            )

        if (
            sales_start_at
            and sales_start_at
            >= event.start_at
        ):
            raise serializers.ValidationError(
                {
                    "sales_start_at": (
                        "Ticket sales must "
                        "start before the event."
                    )
                }
            )

        if (
            sales_end_at
            and sales_end_at
            > event.start_at
        ):
            raise serializers.ValidationError(
                {
                    "sales_end_at": (
                        "Ticket sales cannot "
                        "end after the event "
                        "starts."
                    )
                }
            )
        return attrs