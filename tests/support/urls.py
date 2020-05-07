from django.conf.urls import url, include
from rest_framework import routers

from .views import (
    ArtistViewSet,
    AlbumViewSet,
    TrackViewSet,
    PaginateViewSet,
    NonJSONPaginateViewSet,
    NonDefaultIdViewSet,
)

router = routers.DefaultRouter()
router.register(r"artist", ArtistViewSet, "artist")
router.register(r"album", AlbumViewSet, "album")
router.register(r"track", TrackViewSet, "track")
router.register(r"paged", PaginateViewSet, "page")
router.register(r"paged-nonjson", NonJSONPaginateViewSet, "page-nonjson")
router.register(r"non-default-id", NonDefaultIdViewSet, "non-default-id")

urlpatterns = [url(r"^api/", include(router.urls))]
