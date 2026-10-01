from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

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

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )