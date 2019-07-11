from copy import deepcopy
from typing import Any, Optional, List, TypeVar, Iterator, Dict, Generic

from rest_framework import serializers

from rest_framework_json_schema.relations import JSONAPIRelationshipField
from rest_framework_json_schema.schema import ResourceObject
from rest_framework_json_schema.transforms import CamelCaseTransform


class BaseModel:
    """
    Base test model.

    We try to do what we can to fake a Django model for the purposes of
    serialization, but not have to depend on a database for testing.

    We also make sure that our code does not *require* models to be Django models.
    """

    id: int

    @property
    def pk(self) -> int:
        """Return the model primary key."""
        return self.id

    # This is used to fake a Django model for the purposes
    # of RelatedField.use_pk_only_optimization. It just
    # needs to return the ID value for foreign keys.
    def serializable_value(self, field_name: str) -> Any:
        """Fake a Django model."""
        try:
            value = getattr(self, field_name)
            return value.id
        except AttributeError:
            return getattr(self, field_name)


class Artist(BaseModel):
    """An artist model."""

    def __init__(self, id: int, first_name: str, last_name: str) -> None:
        """Create the object."""
        self.id = id
        self.first_name = first_name
        self.last_name = last_name

    def update(self, id: int, first_name: str, last_name: str) -> None:
        """Update the object."""
        self.first_name = first_name
        self.last_name = last_name


class Album(BaseModel):
    """An album model."""

    def __init__(
        self,
        id: int,
        album_name: str,
        artist: Optional[Artist],
        tracks: Optional[List["Track"]] = None,
    ):
        """Create the object."""
        self.id = id
        self.album_name = album_name
        self.artist = artist

    @property
    def tracks(self) -> List["Track"]:
        """Return the tracks for this album."""
        return [track for track in TRACKS if track.album.id == self.id]


class Track(BaseModel):
    """A track mode."""

    def __init__(self, id: int, track_num: int, name: str, album: Album) -> None:
        """Create the object."""
        self.id = id
        self.track_num = track_num
        self.name = name
        self.album = album


INITIAL_ARTISTS: List[Artist] = [
    Artist(0, "Miles", "Davis"),
    Artist(1, "John", "Coltrane"),
    Artist(2, "Charles", "Mingus"),
    Artist(3, "Bill", "Evans"),
    Artist(4, "Max", "Roach"),
    Artist(5, "Sun", "Ra"),
]
ARTISTS: List[Artist] = []

INITIAL_ALBUMS: List[Album] = [
    Album(0, "A Love Supreme", INITIAL_ARTISTS[1]),
    Album(1, "Birth of the Cool", INITIAL_ARTISTS[0]),
    Album(2, "Space is the Place", INITIAL_ARTISTS[5]),
    Album(3, "Unknown Artist", None),
]
ALBUMS: List[Album] = []

INITIAL_TRACKS: List[Track] = [
    Track(0, 1, "Jeru", INITIAL_ALBUMS[1]),
    Track(1, 2, "Moon Dreams", INITIAL_ALBUMS[1]),
    Track(2, 3, "Venus de Milo", INITIAL_ALBUMS[1]),
    Track(3, 4, "Deception", INITIAL_ALBUMS[1]),
]
TRACKS: List[Track] = []


T = TypeVar("T")


class QuerySet(Generic[T]):
    """Fake a Django queryset."""

    def __init__(self, objs: List[T]) -> None:
        """Initialize with a list of models."""
        self.objs = objs

    def __iter__(self) -> Iterator[T]:
        """Iterate through all models."""
        return iter(self.objs)

    def get(self, pk: int) -> T:
        """Get a model by ID."""
        return self.objs[pk]

    def add(self, obj: T) -> None:
        """Add a model."""
        self.objs.append(obj)

    def count(self) -> int:
        """Get a count of models (used by pagination)."""
        return len(self.objs)

    def __getitem__(self, item: int) -> T:
        """Get an item (used in slicing)."""
        return self.objs[item]


def get_artists() -> QuerySet:
    """Get all artists."""
    return QuerySet(ARTISTS)


def get_albums() -> QuerySet:
    """Get all albums."""
    return QuerySet(ALBUMS)


def get_tracks() -> QuerySet:
    """Get all tracks."""
    return QuerySet(TRACKS)


def reset_data() -> None:
    """Reset test data."""
    global ARTISTS
    global ALBUMS
    global TRACKS
    ARTISTS = deepcopy(INITIAL_ARTISTS)
    ALBUMS = deepcopy(INITIAL_ALBUMS)
    TRACKS = deepcopy(INITIAL_TRACKS)


reset_data()


class ArtistObject(ResourceObject):
    """Resource object for artists."""

    type = "artist"
    attributes = ("first_name", "last_name")
    transformer = CamelCaseTransform


class AlbumObject(ResourceObject):
    """Resource object for albums."""

    type = "album"
    attributes = ("album_name",)
    relationships = ("artist", "tracks")
    transformer = CamelCaseTransform


class TrackObject(ResourceObject):
    """Resource object for tracks."""

    type = "track"
    attributes = ("track_num", "name")
    relationships = ("album",)
    transformer = CamelCaseTransform


class ArtistSerializer(serializers.Serializer):
    """Serializer for artist models."""

    id = serializers.CharField(required=False)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    schema = ArtistObject

    def create(self, validated_data: Dict) -> Dict:
        """Create an artist model."""
        validated_data["id"] = get_artists().count()
        get_artists().add(Artist(**validated_data))
        return validated_data

    def update(self, instance: Artist, validated_data: Dict) -> Artist:
        """Update an artist model."""
        instance.update(**validated_data)
        return instance


class TrackSerializer(serializers.Serializer):
    """Serializer for track models."""

    id = serializers.CharField(required=False)
    track_num = serializers.IntegerField()
    name = serializers.CharField()
    album = JSONAPIRelationshipField(
        serializer="tests.support.serializers.AlbumSerializer", queryset=get_albums()
    )

    schema = TrackObject


class AlbumSerializer(serializers.Serializer):
    """Serializer for album models."""

    id = serializers.CharField(required=False)
    album_name = serializers.CharField()
    artist = JSONAPIRelationshipField(
        serializer=ArtistSerializer, queryset=get_artists()
    )
    tracks = JSONAPIRelationshipField(
        serializer=TrackSerializer, many=True, queryset=get_tracks()
    )

    schema = AlbumObject

    def create(self, validated_data: Dict) -> Dict:
        """Create an album model."""
        validated_data["id"] = get_albums().count()
        get_albums().add(Album(**validated_data))
        return validated_data
