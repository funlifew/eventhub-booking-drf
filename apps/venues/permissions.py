from rest_framework.permissions import (
    SAFE_METHODS,
    BasePermission,
)

class IsVenueOwnerOrAdmin(
    BasePermission
):
    message = (
        "You do not have permission "
        "to modify this venue."
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
            obj.created_by_id
            == user.id
        )