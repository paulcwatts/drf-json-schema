from django.conf.urls import url, include
from rest_framework import routers
from .views import ArtistViewSet, AlbumViewSet, TrackViewSet, PaginateViewSet


router = routers.DefaultRouter()
router.register(r'artist', ArtistViewSet, 'artist')
router.register(r'album', AlbumViewSet, 'album')
router.register(r'track', TrackViewSet, 'track')
router.register(r'paged', PaginateViewSet, 'page')

urlpatterns = [
    url(r'^api/', include(router.urls))
]
