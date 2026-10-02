from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel

class Venue(TimeStampedModel):
    name = models.CharField(
        max_length=200,
    )
    
    country = models.CharField(
        max_length=100,
        default="Iran",
    )
    
    city = models.CharField(
        max_length=100,
        default="Tehran",
    )
    
    address = models.TextField()

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
        ],
        help_text=(
            "Maximum physical capacity "
            "of the venue."
        ),
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_venues',
        null=True,
        blank=True,
    )
    
    is_active = models.BooleanField(
        default=True,
    )
    
    class Meta:
        ordering = [
            'name',
            'id',
        ]
        
        indexes = [
            models.Index(
                fields=[
                    'city',
                    'is_active',
                ],
            ),
            models.Index(
                fields=[
                    "country",
                    "city",
                ],
            ),
            models.Index(
                fields=[
                    'is_active',
                ],
            ),
        ]
        
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(capacity__isnull=True)
                    | Q(capacity__gt=0)
                ),
                name="venues_capacity_gt_zero_or_null",
            ),
        ]
    
    
    def __str__(self):
        return f"{self.name} - {self.city}"