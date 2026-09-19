import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import TimeStampedModel
from apps.events.models import TicketType


class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', "Pending"
        CONFIRMED = 'confirmed', "Confirmed"
        CANCELLED = 'cancelled', "Cancelled"
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    
    ticket_type = models.ForeignKey(
        TicketType,
        on_delete=models.PROTECT,
        related_name='bookings',
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
    )
    
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    
    class Meta:
        ordering = ['-created_at']
        
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['ticket_type']),
            models.Index(fields=['created_at']),
        ]
        
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name='booking_quantity_gt_zero',
            ),
        ]
    
    @property
    def total_price(self):
        return self.unit_price * self.quantity
    
    @property
    def event(self):
        return self.ticket_type.event
    
    def __str__(self):
        return f"{self.user} - {self.ticket_type} - {self.quantity}"