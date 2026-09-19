from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        'api/v1/users/',
        include(
            'apps.users.urls',
            namespace='users',
        )
    ),
    path(
        'api/v1/bookings/',
        include(
            'apps.bookings.urls',
            namespace='bookings',
        )
    ),
    path(
        'api/v1/events/',
        include(
            'apps.events.urls',
            namespace='events',
        )
    ),
    path(
        'api/v1/venues/',
        include(
            'apps.venues.urls',
            namespace='venues',
        )
    ),
]
