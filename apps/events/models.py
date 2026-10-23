from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q

from apps.core.models import TimeStampedModel
from apps.venues.models import Venue


class Event(TimeStampedModel):
    class Category(models.TextChoices):
        MUSIC = "music", "Music"
        TECHNOLOGY = "technology", "Technology"
        ART = "art", "Art"
        SPORT = "sport", "Sport"
        EDUCATION = "education", "Education"
        BUSINESS = "business", "Business"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    title = models.CharField(
        max_length=200,
    )

    description = models.TextField()

    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="events",
    )

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    start_at = models.DateTimeField()

    end_at = models.DateTimeField()

    banner = models.ImageField(
        upload_to="events/banners/",
        blank=True,
        null=True,
    )

    is_featured = models.BooleanField(
        default=False,
    )

    class Meta:
        ordering = [
            "start_at",
            "id",
        ]

        indexes = [
            models.Index(
                fields=[
                    "status",
                    "start_at",
                ],
            ),
            models.Index(
                fields=[
                    "venue",
                    "status",
                ],
            ),
            models.Index(
                fields=[
                    "category",
                    "status",
                ],
            ),
            models.Index(
                fields=[
                    "is_featured",
                    "status",
                ],
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    end_at__gt=F("start_at")
                ),
                name="event_end_after_start",
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.start_at
            and self.end_at
            and self.end_at <= self.start_at
        ):
            raise ValidationError(
                {
                    "end_at": (
                        "Event end time must be "
                        "after its start time."
                    )
                }
            )

    def __str__(self):
        return self.title


class TicketType(TimeStampedModel):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="ticket_types",
    )

    name = models.CharField(
        max_length=100,
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )

    capacity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    max_per_booking = (
        models.PositiveIntegerField(
            default=5,
            validators=[
                MinValueValidator(1),
            ],
        )
    )

    sales_start_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    sales_end_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(
        default=True,
    )

    class Meta:
        ordering = [
            "price",
            "id",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "event",
                    "name",
                ],
                name=(
                    "unique_ticket_type_"
                    "name_per_event"
                ),
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name=(
                    "ticket_price_gte_zero"
                ),
            ),
            models.CheckConstraint(
                condition=Q(capacity__gt=0),
                name=(
                    "ticket_capacity_gt_zero"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    max_per_booking__gt=0
                ),
                name=(
                    "ticket_max_per_booking_"
                    "gt_zero"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    max_per_booking__lte=F(
                        "capacity"
                    )
                ),
                name=(
                    "ticket_max_per_booking_"
                    "lte_capacity"
                ),
            ),
        ]

    def clean(self):
        super().clean()

        if (
            self.sales_start_at
            and self.sales_end_at
            and self.sales_end_at
            <= self.sales_start_at
        ):
            raise ValidationError(
                {
                    "sales_end_at": (
                        "Ticket sales end time "
                        "must be after the sales "
                        "start time."
                    )
                }
            )

        if (
            self.sales_start_at
            and self.event_id
            and self.sales_start_at
            >= self.event.start_at
        ):
            raise ValidationError(
                {
                    "sales_start_at": (
                        "Ticket sales must begin "
                        "before the event starts."
                    )
                }
            )

        if (
            self.sales_end_at
            and self.event_id
            and self.sales_end_at
            > self.event.start_at
        ):
            raise ValidationError(
                {
                    "sales_end_at": (
                        "Ticket sales cannot end "
                        "after the event starts."
                    )
                }
            )

    def __str__(self):
        return (
            f"{self.event.title} - "
            f"{self.name}"
        )