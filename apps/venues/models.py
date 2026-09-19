from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel

# Create your models here.

class Venue(TimeStampedModel):
    name = models.CharField(
        max_length=200,
    )
    
    country = models.CharField(
        max_length=100,
        default='Iran',
    )
    
    city = models.CharField(
        max_length=100,
        default="Tehran",
    )
    
    address = models.TextField()

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Maximum physical capacity of the venue.',
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
    
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    
    class Meta:
        ordering = ['name']

        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"
