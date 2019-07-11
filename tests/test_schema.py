from collections import OrderedDict
from typing import Any, Dict

import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from rest_framework_json_schema.exceptions import TypeConflict, IncludeInvalid
from rest_framework_json_schema.schema import (
    Context,
    ResourceObject,
    RelationshipObject,
    ResourceIdObject,
    LinkObject,
    UrlLink,
    ObjDataType,
)
from rest_framework_json_schema.transforms import CamelCaseTransform
from rest_framework_json_schema.utils import parse_include
from tests.support.decorators import mark_urls


@pytest.fixture
def schema_request(factory: APIRequestFactory) -> Request:
    factory = APIRequestFactory()
    return factory.get("/")


@pytest.fixture
def context(schema_request: Request) -> Context:
    return Context(schema_request)


@mark_urls
def test_resource_object_default(context: Context) -> None:
    """With no attributes, nothing is included, just the ID."""
    primary, included = ResourceObject().render(
        {"id": "123", "attribute": "ignored"}, context
    )
    assert primary == OrderedDict((("id", "123"), ("type", "unknown")))
    assert included == []


@mark_urls
def test_constructor(context: Context) -> None:
    """You can specify the schema using the constructor."""
    obj = ResourceObject(id="user_id", type="users", attributes=("name",))
    primary, included = obj.render({"user_id": "123", "name": "John"}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "users"),
            ("attributes", OrderedDict((("name", "John"),))),
        )
    )
    assert included == []


@mark_urls
def test_subclass(context: Context) -> None:
    """You can use a subclass to specify schema information."""

    class TestObject(ResourceObject):
        id = "user_id"
        type = "users"
        attributes = ("name",)

    primary, included = TestObject().render({"user_id": "123", "name": "John"}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "users"),
            ("attributes", OrderedDict((("name", "John"),))),
        )
    )
    assert included == []


@mark_urls
def test_links(context: Context) -> None:
    """You can specify links which are methods on the object."""

    class ObjectLink(LinkObject):
        def render(self, data: ObjDataType, request: Request) -> Any:
            return {"href": "/users/%s" % data["id"], "meta": {"something": "hello"}}

    class TestObject(ResourceObject):
        type = "artists"
        links = (
            ("self", UrlLink(view_name="artist-detail", url_kwargs={"pk": "id"})),
            (
                "relative",
                UrlLink(
                    view_name="artist-detail", url_kwargs={"pk": "id"}, absolute=False
                ),
            ),
            ("object", ObjectLink()),
        )

    primary, included = TestObject().render({"id": "123"}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "artists"),
            (
                "links",
                OrderedDict(
                    (
                        ("self", "http://testserver/api/artist/123/"),
                        ("relative", "/api/artist/123/"),
                        (
                            "object",
                            {"href": "/users/123", "meta": {"something": "hello"}},
                        ),
                    )
                ),
            ),
        )
    )
    assert included == []


@mark_urls
def test_meta(context: Context) -> None:
    """An optional meta object is rendered."""
    obj = ResourceObject(type="users", meta={"foo": "bar"})
    primary, included = obj.render({"id": "123"}, context)
    assert primary == OrderedDict(
        (("id", "123"), ("type", "users"), ("meta", {"foo": "bar"}))
    )
    assert included == []


@mark_urls
def test_render_relationships(context: Context) -> None:
    """Test that relationships can be rendered with their associated metadata."""

    class AlbumObject(ResourceObject):
        type = "album"
        relationships = ("artist",)

    # Empty to-one relationship: relationship is 'None'
    # Empty to-many relationship: relationship is '[]'
    # Single relationship: a ResourceIdObject
    # To-Many: an array of ResourceIdObjects
    obj = AlbumObject()

    primary, included = obj.render({"id": "123", "artist": None}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict((("artist", OrderedDict((("data", None),))),)),
            ),
        )
    )
    assert included == []

    primary, included = obj.render({"id": "123", "artist": []}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            ("relationships", OrderedDict((("artist", OrderedDict((("data", []),))),))),
        )
    )
    assert included == []

    primary, included = obj.render(
        {"id": "123", "artist": ResourceIdObject(id=5, type="artist")}, context
    )
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict(
                    (
                        (
                            "artist",
                            OrderedDict(
                                (
                                    (
                                        "data",
                                        OrderedDict((("id", "5"), ("type", "artist"))),
                                    ),
                                )
                            ),
                        ),
                    )
                ),
            ),
        )
    )
    assert included == []

    primary, included = obj.render(
        {
            "id": "123",
            "artist": [
                ResourceIdObject(id=5, type="artist"),
                ResourceIdObject(id=6, type="artist"),
            ],
        },
        context,
    )
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict(
                    (
                        (
                            "artist",
                            OrderedDict(
                                (
                                    (
                                        "data",
                                        [
                                            OrderedDict(
                                                (("id", "5"), ("type", "artist"))
                                            ),
                                            OrderedDict(
                                                (("id", "6"), ("type", "artist"))
                                            ),
                                        ],
                                    ),
                                )
                            ),
                        ),
                    )
                ),
            ),
        )
    )
    assert included == []


@mark_urls
def test_render_complex_relationship(context: Context) -> None:
    """
    Allow specifying a relationship object that specifies additional data for the relationship.

    Relationship links will most likely depend on some part of original object's data
    (like the pk)
    """

    class ArtistRelationship(RelationshipObject):
        links = (
            (
                "self",
                UrlLink(view_name="album-relationship-artist", url_kwargs={"pk": "id"}),
            ),
            (
                "related",
                UrlLink(view_name="album-related-artist", url_kwargs={"pk": "id"}),
            ),
        )
        meta = {"foo": "bar"}

    class AlbumObject(ResourceObject):
        type = "album"
        relationships = (("album_artist", ArtistRelationship()),)
        transformer = CamelCaseTransform

    obj = AlbumObject()

    primary, included = obj.render({"id": "123", "album_artist": None}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict(
                    (
                        (
                            "albumArtist",
                            OrderedDict(
                                (
                                    ("data", None),
                                    (
                                        "links",
                                        OrderedDict(
                                            (
                                                (
                                                    "self",
                                                    "http://testserver/api/album/123/relationship_artist/",
                                                ),
                                                (
                                                    "related",
                                                    "http://testserver/api/album/123/related_artist/",
                                                ),
                                            )
                                        ),
                                    ),
                                    ("meta", {"foo": "bar"}),
                                )
                            ),
                        ),
                    )
                ),
            ),
        )
    )
    assert included == []


@mark_urls
def test_tolerate_missing_attributes(context: Context) -> None:
    """To support write_only data, be tolerant if an attribute isn't in the data."""
    obj = ResourceObject(
        id="user_id", type="users", attributes=("first_name", "last_name")
    )
    primary, included = obj.render({"user_id": "123", "first_name": "John"}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "users"),
            ("attributes", OrderedDict((("first_name", "John"),))),
        )
    )
    assert included == []


@mark_urls
def test_tolerate_missing_relationships(context: Context) -> None:
    """To support write_only data, be tolerant if a relationship isn't in the data."""

    class AlbumObject(ResourceObject):
        type = "album"
        relationships = ("artist", "artist2")

    # Empty to-one relationship: relationship is 'None'
    # Empty to-many relationship: relationship is '[]'
    # Single relationship: a ResourceIdObject
    # To-Many: an array of ResourceIdObjects
    obj = AlbumObject()

    primary, included = obj.render({"id": "123", "artist2": None}, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict((("artist2", OrderedDict((("data", None),))),)),
            ),
        )
    )
    assert included == []


@mark_urls
def test_render_included(schema_request: Request) -> None:
    """You can render included resources."""

    class ArtistObject(ResourceObject):
        type = "artist"
        attributes = ("first_name", "last_name")

    class AlbumObject(ResourceObject):
        type = "album"
        relationships = ("artist",)

    # This a faked ResourceIdObject that allows you the schema to not know about
    # the serializer directly.
    class ArtistLink(ResourceIdObject):
        def get_schema(self) -> ResourceObject:
            return ArtistObject()

        def get_data(self) -> Dict[str, Any]:
            return {"id": self.id, "first_name": "John", "last_name": "Coltrane"}

    primary, included = AlbumObject().render(
        {"id": "123", "artist": ArtistLink(id=5, type="artist")},
        Context(schema_request, parse_include("artist")),
    )
    assert included == [
        OrderedDict(
            (
                ("id", "5"),
                ("type", "artist"),
                (
                    "attributes",
                    OrderedDict((("first_name", "John"), ("last_name", "Coltrane"))),
                ),
            )
        )
    ]


@mark_urls
def test_render_included_path(schema_request: Request) -> None:
    """You can render included paths."""

    class ArtistObject(ResourceObject):
        type = "artist"
        attributes = ("first_name", "last_name")
        relationships = ("albums",)

    class AlbumObject(ResourceObject):
        type = "album"
        attributes = ("name",)
        relationships = ("tracks",)

    class TrackObject(ResourceObject):
        type = "track"
        attributes = ("name",)

    class TrackLink(ResourceIdObject):
        type: str = "track"
        name: str = ""

        def get_schema(self) -> ResourceObject:
            return TrackObject()

        def get_data(self) -> Dict[str, Any]:
            return {"id": self.id, "name": self.name}

    # This a faked ResourceIdObject that allows you the schema to not know about
    # the serializer directly.
    class AlbumLink(ResourceIdObject):
        type = "album"
        name: str = ""

        def get_schema(self) -> ResourceObject:
            return AlbumObject()

        def get_data(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "name": self.name,
                "tracks": [
                    TrackLink(id=1, name="Acknowledgement"),
                    TrackLink(id=2, name="Resolution"),
                ],
            }

    primary, included = ArtistObject().render(
        {
            "id": "123",
            "first_name": "John",
            "last_name": "Coltrane",
            "albums": [AlbumLink(id=5, name="A Love Supreme")],
        },
        Context(schema_request, parse_include("albums.tracks")),
    )
    assert included == [
        OrderedDict(
            (
                ("id", "5"),
                ("type", "album"),
                ("attributes", OrderedDict((("name", "A Love Supreme"),))),
                (
                    "relationships",
                    OrderedDict(
                        (
                            (
                                "tracks",
                                OrderedDict(
                                    (
                                        (
                                            "data",
                                            [
                                                OrderedDict(
                                                    (("id", "1"), ("type", "track"))
                                                ),
                                                OrderedDict(
                                                    (("id", "2"), ("type", "track"))
                                                ),
                                            ],
                                        ),
                                    )
                                ),
                            ),
                        )
                    ),
                ),
            )
        ),
        OrderedDict(
            (
                ("id", "1"),
                ("type", "track"),
                ("attributes", OrderedDict((("name", "Acknowledgement"),))),
            )
        ),
        OrderedDict(
            (
                ("id", "2"),
                ("type", "track"),
                ("attributes", OrderedDict((("name", "Resolution"),))),
            )
        ),
    ]


@mark_urls
def test_render_invalid_include(schema_request: Request) -> None:
    """An invalid include path throws an exception."""

    class ArtistObject(ResourceObject):
        type = "artist"
        attributes = ("first_name", "last_name")
        relationships = ("albums",)

    with pytest.raises(IncludeInvalid):
        ArtistObject().render(
            {"id": "123", "first_name": "John", "last_name": "Coltrane", "albums": []},
            Context(schema_request, parse_include("invalid")),
        )


@mark_urls
def test_render_sparse_fields(schema_request: Request) -> None:
    """Specifying sparse fields limits the rendered attributes/relationships."""

    class ArtistObject(ResourceObject):
        type = "artist"
        attributes = ("first_name", "last_name")

    class AlbumObject(ResourceObject):
        type = "album"
        attributes = ("name", "genre")
        relationships = ("artist",)

    # This a faked ResourceIdObject that allows the schema to not know about
    # the serializer directly.
    class ArtistLink(ResourceIdObject):
        def get_schema(self) -> ResourceObject:
            return ArtistObject()

        def get_data(self) -> Dict[str, Any]:
            return {"id": self.id, "first_name": "John", "last_name": "Coltrane"}

    obj = {
        "id": "123",
        "name": "A Love Supreme",
        "genre": "Jazz",
        "artist": ArtistLink(id=5, type="artist"),
    }

    context = Context(schema_request, fields={"album": ["name"]})
    primary, included = AlbumObject().render(obj, context)

    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            ("attributes", OrderedDict((("name", "A Love Supreme"),))),
        )
    )
    assert included == []

    # Sparse relationship
    context = Context(schema_request, fields={"album": ["artist"]})
    primary, included = AlbumObject().render(obj, context)
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            (
                "relationships",
                OrderedDict(
                    (
                        (
                            "artist",
                            OrderedDict(
                                (
                                    (
                                        "data",
                                        OrderedDict((("id", "5"), ("type", "artist"))),
                                    ),
                                )
                            ),
                        ),
                    )
                ),
            ),
        )
    )

    # Include a relationship with sparse fields specified for that relationship
    context = Context(
        schema_request, parse_include("artist"), {"artist": ["first_name"]}
    )
    primary, included = AlbumObject().render(obj, context)
    assert included == [
        OrderedDict(
            (
                ("id", "5"),
                ("type", "artist"),
                ("attributes", OrderedDict((("first_name", "John"),))),
            )
        )
    ]


@mark_urls
def test_sparse_transformed_fields(schema_request: Request) -> None:
    """Test that the transformed sparse field names are used."""

    class ArtistObject(ResourceObject):
        type = "artist"
        attributes = ("first_name", "last_name")
        transformer = CamelCaseTransform

    class AlbumObject(ResourceObject):
        type = "album"
        attributes = ("album_name", "genre")
        relationships = ("artist",)
        transformer = CamelCaseTransform

    # This a faked ResourceIdObject that allows the schema to not know about
    # the serializer directly.
    class ArtistLink(ResourceIdObject):
        def get_schema(self) -> ResourceObject:
            return ArtistObject()

        def get_data(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "first_name": "John",
                "last_name": "Coltrane",
                "instrument": "Saxophone",
            }

    obj = {
        "id": "123",
        "album_name": "A Love Supreme",
        "genre": "Jazz",
        "artist": ArtistLink(id=5, type="artist"),
    }
    context = Context(schema_request, fields={"album": ["albumName"]})
    primary, included = AlbumObject().render(obj, context)

    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "album"),
            ("attributes", OrderedDict((("albumName", "A Love Supreme"),))),
        )
    )


@mark_urls
def test_transform(context: Context) -> None:
    """You can specify and transform that adjusts the names."""
    obj = ResourceObject(
        type="users",
        attributes=("first_name", "last_name"),
        transformer=CamelCaseTransform,
    )
    primary, included = obj.render(
        {"id": "123", "first_name": "John", "last_name": "Coltrane"}, context
    )
    assert primary == OrderedDict(
        (
            ("id", "123"),
            ("type", "users"),
            (
                "attributes",
                OrderedDict((("firstName", "John"), ("lastName", "Coltrane"))),
            ),
        )
    )
    assert included == []


@mark_urls
def test_parse(context: Context) -> None:
    """Tests parsing attributes with transforms."""
    obj = ResourceObject(
        type="users",
        attributes=("first_name", "last_name"),
        transformer=CamelCaseTransform,
    )
    result = obj.parse(
        {
            "id": "123",
            "type": "users",
            "attributes": {"firstName": "John", "lastName": "Coltrane"},
        },
        context,
    )
    assert result == {"id": "123", "first_name": "John", "last_name": "Coltrane"}


@mark_urls
def test_parse_partial(context: Context) -> None:
    """Attributes not passed in don't get included in the result data."""
    obj = ResourceObject(
        type="users",
        attributes=("first_name", "last_name"),
        transformer=CamelCaseTransform,
    )
    result = obj.parse({"type": "users", "attributes": {"firstName": "John"}}, context)
    assert result == {"first_name": "John"}


@mark_urls
def test_parse_type_conflict(schema_request: Request) -> None:
    """
    The parser throws a type conflict exception on type conflicts.
    """
    obj = ResourceObject(type="users")
    with pytest.raises(TypeConflict):
        obj.parse({"id": "123", "type": "something"}, Context(schema_request))
    with pytest.raises(TypeConflict):
        obj.parse({}, schema_request)
