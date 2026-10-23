from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
)

class IsEventOwnerOrAdmin(
    BasePermission
):
    message = (
        "You do not have permission "
        "to manage this event."
    )
    
    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if request.method in SAFE_METHODS:
            return True
        
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if (
            user.is_staff
            or user.is_superuser
        ):
            return True
        
        return (
            obj.venue.created_by_id
            == user.id
        )

class IsTicketTypeOwnerOrAdmin(
    BasePermission
):
    message = (
        "You do not have permission "
        "to manage this ticket type."
    )
    
    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        if request.method in SAFE_METHODS:
            return True
        
        user = request.user
        
        if not user.is_authenticated:
            return False
        
        if (
            user.is_staff
            or user.is_superuser
        ):
            return True
        
        
        return (
            obj.event.venue.created_by_id
            == user.id
        )