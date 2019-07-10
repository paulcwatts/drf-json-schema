import json

from django.urls import reverse
from rest_framework.test import APIRequestFactory

from tests.support.decorators import mark_urls
from tests.support.views import ArtistViewSet, AlbumViewSet, TrackViewSet


@mark_urls
def test_detail_attributes(factory: APIRequestFactory) -> None:
    """You can render primary data object attributes."""
    request = factory.get(reverse("artist-detail", kwargs={"pk": 1}))
    view_detail = ArtistViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=1)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "1",
            "type": "artist",
            "attributes": {"firstName": "John", "lastName": "Coltrane"},
        }
    }


@mark_urls
def test_list_attributes(factory: APIRequestFactory) -> None:
    """You can render primary data list attributes."""
    request = factory.get(reverse("artist-list"))
    view_list = ArtistViewSet.as_view({"get": "list"})
    response = view_list(request)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"

    data = json.loads(response.content)["data"]
    assert data[:3] == [
        {
            "id": "0",
            "type": "artist",
            "attributes": {"firstName": "Miles", "lastName": "Davis"},
        },
        {
            "id": "1",
            "type": "artist",
            "attributes": {"firstName": "John", "lastName": "Coltrane"},
        },
        {
            "id": "2",
            "type": "artist",
            "attributes": {"firstName": "Charles", "lastName": "Mingus"},
        },
    ]


@mark_urls
def test_empty_list(factory: APIRequestFactory) -> None:
    """The 'data' field appears in the top-level object even if data is empty."""
    request = factory.get(reverse("artist-list"), {"filter[firstName]": "Foo"})
    view_list = ArtistViewSet.as_view({"get": "list"})
    response = view_list(request)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {"data": []}


@mark_urls
def test_attributes_exception(factory: APIRequestFactory) -> None:
    """The renderer handles thrown exceptions."""
    request = factory.get(reverse("artist-detail", kwargs={"pk": 8}))
    view_detail = ArtistViewSet.as_view({"get": "retrieve"})

    response = view_detail(request, pk=8)
    response.render()
    assert json.loads(response.content.decode()) == {
        "errors": [{"detail": "Not found."}]
    }


@mark_urls
def test_attributes_options(factory: APIRequestFactory) -> None:
    """You can specify options in meta."""
    request = factory.options(reverse("artist-list"))
    view_list = ArtistViewSet.as_view({"get": "list"})

    response = view_list(request)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "meta": {
            "data": {
                "description": "A simple ViewSet for listing or retrieving artists.",
                "name": "Artist",
                "parses": ["application/vnd.api+json"],
                "renders": ["application/vnd.api+json"],
            }
        }
    }


@mark_urls
def test_attributes_fields(factory: APIRequestFactory) -> None:
    """The fields attribute returns specific fields."""
    url = reverse("artist-detail", kwargs={"pk": 1})
    request = factory.get(url, {"fields[artist]": "firstName"})
    view_detail = ArtistViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=1)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {"id": "1", "type": "artist", "attributes": {"firstName": "John"}}
    }


@mark_urls
def test_relationships_empty(factory: APIRequestFactory) -> None:
    """You can render empty relationships."""
    request = factory.get(reverse("album-detail", kwargs={"pk": 3}))
    view_detail = AlbumViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=3)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "3",
            "type": "album",
            "attributes": {"albumName": "Unknown Artist"},
            "relationships": {"artist": {"data": None}, "tracks": {"data": []}},
        }
    }


@mark_urls
def test_to_one_non_empty(factory: APIRequestFactory) -> None:
    """You can render a non-empty to-one relationship."""
    request = factory.get(reverse("album-detail", kwargs={"pk": 0}))
    view_detail = AlbumViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=0)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "0",
            "type": "album",
            "attributes": {"albumName": "A Love Supreme"},
            "relationships": {
                "artist": {"data": {"id": "1", "type": "artist"}},
                "tracks": {"data": []},
            },
        }
    }


@mark_urls
def test_to_many_non_empty(factory: APIRequestFactory) -> None:
    """You can render a non-empty to-many relationship."""
    request = factory.get(reverse("album-detail", kwargs={"pk": 1}))
    view_detail = AlbumViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=1)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "1",
            "type": "album",
            "attributes": {"albumName": "Birth of the Cool"},
            "relationships": {
                "artist": {"data": {"id": "0", "type": "artist"}},
                "tracks": {
                    "data": [
                        {"id": "0", "type": "track"},
                        {"id": "1", "type": "track"},
                        {"id": "2", "type": "track"},
                        {"id": "3", "type": "track"},
                    ]
                },
            },
        }
    }


@mark_urls
def test_include_to_one(factory: APIRequestFactory) -> None:
    """You can include a to-one relationship as a compound document."""
    request = factory.get(
        reverse("album-detail", kwargs={"pk": 0}), {"include": "artist"}
    )
    view_detail = AlbumViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=0)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "0",
            "type": "album",
            "attributes": {"albumName": "A Love Supreme"},
            "relationships": {
                "artist": {"data": {"id": "1", "type": "artist"}},
                "tracks": {"data": []},
            },
        },
        "included": [
            {
                "id": "1",
                "type": "artist",
                "attributes": {"firstName": "John", "lastName": "Coltrane"},
            }
        ],
    }


@mark_urls
def test_include_to_many_and_paths(factory: APIRequestFactory) -> None:
    """You can include a to-many relationship as a compound document."""
    track_detail = TrackViewSet.as_view({"get": "retrieve"})
    request = factory.get(
        reverse("track-detail", kwargs={"pk": 0}),
        {"include": "album,album.artist,album.tracks"},
    )
    response = track_detail(request, pk=0)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "0",
            "type": "track",
            "attributes": {"name": "Jeru", "trackNum": 1},
            "relationships": {"album": {"data": {"id": "1", "type": "album"}}},
        },
        "included": [
            {
                "id": "1",
                "type": "album",
                "attributes": {"albumName": "Birth of the Cool"},
                "relationships": {
                    "artist": {"data": {"id": "0", "type": "artist"}},
                    "tracks": {
                        "data": [
                            {"id": "0", "type": "track"},
                            {"id": "1", "type": "track"},
                            {"id": "2", "type": "track"},
                            {"id": "3", "type": "track"},
                        ]
                    },
                },
            },
            {
                "id": "0",
                "type": "artist",
                "attributes": {"firstName": "Miles", "lastName": "Davis"},
            },
            {
                "id": "0",
                "type": "track",
                "attributes": {"name": "Jeru", "trackNum": 1},
                "relationships": {"album": {"data": {"id": "1", "type": "album"}}},
            },
            {
                "id": "1",
                "type": "track",
                "attributes": {"name": "Moon Dreams", "trackNum": 2},
                "relationships": {"album": {"data": {"id": "1", "type": "album"}}},
            },
            {
                "id": "2",
                "type": "track",
                "attributes": {"name": "Venus de Milo", "trackNum": 3},
                "relationships": {"album": {"data": {"id": "1", "type": "album"}}},
            },
            {
                "id": "3",
                "type": "track",
                "attributes": {"name": "Deception", "trackNum": 4},
                "relationships": {"album": {"data": {"id": "1", "type": "album"}}},
            },
        ],
    }


@mark_urls
def test_relationships_fields(factory: APIRequestFactory) -> None:
    """You can use fields to specify specific relationships fields."""
    request = factory.get(
        reverse("album-detail", kwargs={"pk": 0}),
        {"fields[album]": "artist", "fields[artist]": "firstName", "include": "artist"},
    )
    view_detail = AlbumViewSet.as_view({"get": "retrieve"})
    response = view_detail(request, pk=0)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"
    assert json.loads(response.content) == {
        "data": {
            "id": "0",
            "type": "album",
            "relationships": {"artist": {"data": {"id": "1", "type": "artist"}}},
        },
        "included": [
            {"id": "1", "type": "artist", "attributes": {"firstName": "John"}}
        ],
    }
