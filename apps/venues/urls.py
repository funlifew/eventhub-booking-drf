from rest_framework.routers import (
    SimpleRouter,
)

from .views import VenueViewSet


app_name = "venues"


router = SimpleRouter()

router.register(
    "",
    VenueViewSet,
    basename="venue",
)


urlpatterns = router.urls