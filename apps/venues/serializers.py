from rest_framework import serializers

from .models import Venue

class VenueSerializer(
    serializers.ModelSerializer
):
    created_by_username = serializers.SerializerMethodField()
    
    events_count = serializers.IntegerField(
        read_only=True,
        default=0,
    )
    
    class Meta:
        model = Venue
        
        fields = (
            "id",
            "name",
            "country",
            "city",
            "address",
            "capacity",
            "created_by",
            "created_by_username",
            "is_active",
            "events_count",
            "created_at",
            "updated_at",
        )
        
        read_only_fields = (
            "id",
            "created_by",
            "created_by_username",
            "is_active",
            "events_count",
            "created_at",
            "updated_at",
        )
        
    
    def get_created_by_username(
        self,
        obj,
    ):
        if obj.created_by is None:
            return None
        
        return obj.created_by.username
    
    def validate_capacity(self, value):
        if (
            value is not None
            and value <= 0
        ):
            raise serializers.ValidationError(
                (
                    "Venue capacity must be "
                    "greater than zero."
                )
            )
        
        return value