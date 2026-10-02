from rest_framework.exceptions import (
    ValidationError,
)
from rest_framework.filters import (
    BaseFilterBackend,
)

class VenueFilterBackend(
    BaseFilterBackend
):
    TRUE_VALUES = (
        "true",
        "1",
        "yes",
    )
    
    FALSE_VALUES = (
        'false',
        '0',
        'no',
    )
    
    def filter_queryset(
        self,
        request,
        queryset,
        view,
    ):
        city = request.query_params.get(
            "city"
        )
        
        country = (
            request.query_params.get(
                "country"
            )
        )
        
        min_capacity = (
            request.query_params.get(
                "min_capacity"
            )
        )
        
        max_capacity = (
            request.query_params.get(
                "max_capacity"
            )
        )
        
        is_active = (
            request.query_params.get(
                'is_active'
            )
        )
        
        if city:
            queryset = queryset.filter(
                city__iexact=city.strip()
            )
        
        if country:
            queryset = queryset.filter(
                country__iexact=country.strip()
            )
        
        if min_capacity is not None:
            min_capacity = self._parse_capacity(
                min_capacity,
                "min_capacity",
            )
            
            queryset = queryset.filter(
                capacity__gte=min_capacity
            )
        
        if max_capacity is not None:
            max_capacity = self._parse_capacity(
                max_capacity,
                "max_capacity",
            )
            
            queryset = queryset.filter(
                capacity__lte=max_capacity
            )
        
        if is_active is not None:
            is_active = self._parse_boolean(is_active)

            queryset = queryset.filter(
                is_active=is_active
            )
        
        return queryset
    
    def _parse_capacity(
        self,
        value,
        field_name,
    ):
        try:
            value = int(value)
        
        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValidationError(
                {
                    field_name: (
                        "Must be an integer."
                    )
                }
            ) from exc
        
        if value < 0:
            raise ValidationError(
                {
                    field_name: (
                        "Must be zero or "
                        "greater."
                    )
                }
            )

        return value

    def _parse_boolean(
        self,
        value,
    ):
        normalized = (
            str(value)
            .strip()
            .lower()
        )

        if normalized in self.TRUE_VALUES:
            return True

        if normalized in self.FALSE_VALUES:
            return False

        raise ValidationError(
            {
                "is_active": (
                    "Must be one of: "
                    "true, false, 1, 0, "
                    "yes, no."
                )
            }
        )
