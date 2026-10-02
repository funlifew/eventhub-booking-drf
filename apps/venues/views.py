from django.db.models import (
    Count,
    Q,
)

from rest_framework import (
    filters,
    status,
    viewsets,
)
from rest_framework.decorators import (
    action,
)
from rest_framework.exceptions import (
    NotAuthenticated,
    ValidationError,
)
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import (
    Response,
)

from apps.core.pagination import (
    StandardResultsSetPagination,
)

from .filters import VenueFilterBackend
from .models import Venue
from .permissions import (
    IsVenueOwnerOrAdmin,
)
from .serializers import (
    VenueSerializer
)


class VenueViewSet(
    viewsets.ModelViewSet
):
    queryset = Venue.objects.all()

    serializer_class = VenueSerializer
    
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsVenueOwnerOrAdmin,
    )
    
    pagination_class = (
        StandardResultsSetPagination
    )
    
    filter_backends = (
        VenueFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    )
    
    search_fields = (
        "name",
        "city",
        "country",
        "address",
        "created_by__username",
    )
    
    ordering_fields = (
        "name",
        "city",
        "country",
        "capacity",
        "created_at",
        "updated_at",
        "events_count",
    )
    
    ordering = (
        "name",
        "id",
    )
    
    def get_queryset(self):
        queryset = (
            Venue.objects
            .select_related(
                "created_by"
            )
            .annotate(
                events_count=Count(
                    "events",
                    distinct=True,
                )
            )
        )
        
        user = self.request.user
        
        mine = (
            self.request
            .query_params
            .get("mine")
        )
        
        mine_requested = (
            self._parse_mine_parameter(
                mine
            )
        )
        
        if (
            self.action == "list"
            and mine_requested
        ):
            if not user.is_authenticated:
                raise NotAuthenticated(
                    (
                        "Authentication is "
                        "required to view your "
                        "venues."
                    )
                )
            
            return queryset.filter(
                created_by=user
            )
        
        if (
            user.is_authenticated
            and (
                user.is_staff
                or user.is_superuser
            )
        ):
            return queryset
        
        if self.action == "list":
            return queryset.filter(
                is_active=True
            )
        
        if not user.is_authenticated:
            return queryset.filter(
                is_active=True
            )
    
        return queryset.filter(
            Q(is_active=True)
            | Q(created_by=user)
        )
    
    def perform_create(
        self,
        serializer,
    ):
        serializer.save(
            created_by=self.request.user
        )
    
    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        venue = self.get_object()

        if venue.is_active:
            venue.is_active = False
            
            venue.save(
                update_fields=[
                    'is_active',
                    'updated_at',
                ]
            )
        
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(
        detail=True,
        methods=['post'],
        url_path='activate',
    )
    def activate(
        self,
        request,
        pk=None,
    ):
        venue = self.get_object()

        if not venue.is_active:
            venue.is_active = True
            
            venue.save(
                update_fields=[
                    'is_active',
                    'updated_at',
                ]
            )
        
        serializer = self.get_serializer(venue)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )
    
    def _parse_mine_parameter(
        self,
        value,
    ):
        if value is None:
            return False
        
        normalized = (
            str(value)
            .strip()
            .lower()
        )
        
        if normalized in {
            'true',
            '1',
            'yes'
        }:
            return True
        
        if normalized in {
            'false',
            '0',
            'no',
        }:
            return False
        
        raise ValidationError(
            {
                "mine": (
                    "Must be one of: "
                    "true, false, 1, 0, "
                    "yes, no."
                )
            }
        )