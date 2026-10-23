from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from rest_framework.exceptions import (
    ValidationError,
)

from .models import Event

@transaction.atomic
def publish_event(event):
    event = (
        Event.objects
        .select_for_update()
        .select_related('venue')
        .get(pk=event.pk)
    )
    
    if event.status != Event.Status.DRAFT:
        raise ValidationError(
            {
                "status": (
                    "Only draft events can "
                    "be published."
                )
            }
        )
    
    if not event.venue.is_active:
        raise ValidationError(
            {
                "venue": (
                    "The venue must be active "
                    "before publishing the event."
                )
            }
        )
    
    if event.start_at <= timezone.now():
        raise ValidationError(
            {
                "start_at": (
                    "A past event cannot "
                    "be published."
                )
            }
        )
    
    active_tickets = (
        event.ticket_types.filter(
            is_active=True,
        )
    )
    
    if not active_tickets.exists():
        raise ValidationError(
            {
                "ticket_types": (
                    "At least one active "
                    "ticket type is required "
                    "before publishing."
                )
            }
        )
    
    total_capacity = (
        active_tickets.aggregate(
            total=Sum("capacity")
        )['total']
        or 0
    )
    
    if (
        event.venue.capacity
        is not None
        and total_capacity
        > event.venue.capacity
    ):
        raise ValidationError(
            {
                "ticket_types": (
                    "Total ticket capacity "
                    "cannot exceed venue "
                    "capacity."
                )
            }
        )
    
    event.status = (
        Event.Status.PUBLISHED
    )
    
    event.save(
        update_fields=[
            'status',
            'updated_at',
        ]
    )
    
    return event

@transaction.atomic
def cancel_event(event):
    event = (
        Event.objects
        .select_for_update()
        .get(pk=event.pk)
    )
    
    if event.status == Event.Status.COMPLETED:
        raise ValidationError(
            {
                "status": (
                    "A completed event "
                    "cannot be canceled."
                )
            }
        )
    
    if event.status == Event.Status.CANCELLED:
        return event
    
    event.status = (
        Event.Status.CANCELLED
    )
    
    event.save(
        update_fields=[
            "status",
            "updated_at",
        ]
    )
    
    return event

@transaction.atomic
def complete_event(event):
    event = (
        Event.objects
        .select_for_update()
        .get(pk=event.pk)
    )
    
    if (
        event.status
        != Event.Status.PUBLISHED
    ):
        raise ValidationError(
            {
                "status": (
                    "Only published events "
                    "can be completed."
                )
            }
        )
    
    if event.end_at > timezone.now():
        raise ValidationError(
            {
                "end_at": (
                    "The event cannot be "
                    "completed before it ends."
                )
            }
        )
    
    event.status = (
        Event.Status.COMPLETED
    )
    
    event.save(
        update_fields=[
            'status',
            'updated_at',
        ]
    )
    
    return event

@transaction.atomic
def save_ticket_type_with_capacity_guard(
    serializer,
    *,
    event,
):
    event = (
        Event.objects
        .select_for_update()
        .select_related('venue')
        .get(pk=event.pk)
    )
    
    if event.status != Event.Status.DRAFT:
        raise ValidationError(
            {
                "event": (
                    "Ticket types can only "
                    "be modified while the "
                    "event is a draft."
                )
            }
        )
    
    instance = serializer.instance
    
    existing_tickets = (
        event.ticket_types().all()
    )
    
    if instance is not None:
        existing_tickets = (
            existing_tickets.exclude(
                pk=instance.pk,
            )
        )
    
    existing_capacity = (
        existing_tickets.aggregate(
            total=Sum('capacity')
        )['total']
        or 0
    )
    
    if instance is None:
        new_capacity = (
            serializer.validated_data[
                'capacity'
            ]
        )
    else:
        new_capacity = (
            serializer.validated_data.get(
                'capacity',
                instance.capacity
            )
        )
        
    
    total_capacity = (
        existing_capacity
        + new_capacity
    )
    
    if (
        event.venue.capacity
        is not None
        and total_capacity
        > event.venue.capacity
    ):
        raise ValidationError(
            {
                "capacity": (
                    "Total ticket capacity "
                    "cannot exceed venue "
                    "capacity."
                )
            }
        )
    
    if instance is None:
        return serializer.save(
            event=event
        )
    
    return serializer.save()