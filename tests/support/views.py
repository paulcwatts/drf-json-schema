from typing import Any, Sequence, Type, Optional

from django.http import Http404
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination, BasePagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from rest_framework_json_schema.filters import get_query_filters
from rest_framework_json_schema.negotiation import JSONAPIContentNegotiation
from rest_framework_json_schema.pagination import JSONAPILimitOffsetPagination
from rest_framework_json_schema.parsers import JSONAPIParser
from rest_framework_json_schema.renderers import JSONAPIRenderer
from rest_framework_json_schema.transforms import CamelCaseToUnderscoreTransform
from .serializers import (
    ArtistSerializer,
    AlbumSerializer,
    TrackSerializer,
    NonDefaultIdSerializer,
    get_artists,
    get_albums,
    get_tracks,
    get_non_default_ids,
    QuerySet,
    Artist,
    Album,
    Track,
    NonDefaultId,
)

try:
    from rest_framework.decorators import action

    action_route = action(detail=True, methods=["get"])
except ImportError:
    from rest_framework.decorators import detail_route

    action_route = detail_route(methods=["get"])


class BaseViewSet(viewsets.ModelViewSet):
    """Base view set for our "models"."""

    parser_classes = (JSONAPIParser,)
    permission_classes = (AllowAny,)
    renderer_classes = (JSONAPIRenderer,)
    content_negotiation_class = JSONAPIContentNegotiation

    def get_object(self) -> Any:
        """Get an object using our faked queryset."""
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        try:
            return self.get_queryset()[self.kwargs[lookup_url_kwarg]]
        except IndexError:
            raise Http404("Not found.")

    def filter_queryset(self, queryset: Sequence) -> Sequence:
        """Filter our queryset using the JSON API filter parameter."""
        filters = get_query_filters(
            self.request.query_params, CamelCaseToUnderscoreTransform()
        )
        for key, value in filters.items():
            queryset = [item for item in queryset if getattr(item, key) == value]

        return queryset


class ArtistViewSet(BaseViewSet):
    """A simple ViewSet for listing or retrieving artists."""

    serializer_class = ArtistSerializer
    # This is not testing pagination
    pagination_class: Optional[Type[BasePagination]] = None

    def get_queryset(self) -> QuerySet[Artist]:
        """Return the list of artists."""
        return get_artists()


class PaginateViewSet(ArtistViewSet):
    """Viewset that implements JSON API pagination."""

    pagination_class = JSONAPILimitOffsetPagination


class NonJSONPaginateViewSet(ArtistViewSet):
    """Tests when a viewset is paginated but without a JSONAPI Paginator."""

    pagination_class = LimitOffsetPagination


class AlbumViewSet(BaseViewSet):
    """A simple ViewSet for listing or retrieving albums."""

    pagination_class = None

    def get_queryset(self) -> QuerySet[Album]:
        """Return the list of albums."""
        return get_albums()

    def get_serializer(self, *args: Any, **kwargs: Any) -> BaseSerializer:
        """Test the use of dynamic serializers with the parser."""
        return AlbumSerializer(*args, **kwargs)

    @action_route
    def relationship_artist(self) -> Response:
        """Do nothing."""
        # Not currently called, just reversed.
        return Response()

    @action_route
    def related_artist(self) -> Response:
        """Do nothing."""
        # Not currently called, just reversed.
        return Response()


class TrackViewSet(BaseViewSet):
    """A simple ViewSet for listing or retrieving tracks."""

    serializer_class = TrackSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[Track]:
        """Return the list of tracks."""
        return get_tracks()


class NonDefaultIdViewSet(BaseViewSet):
    """A ViewSet to test non-default IDs."""

    serializer_class = NonDefaultIdSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet[NonDefaultId]:
        """Return the list of non default ID objects."""
        return get_non_default_ids()
