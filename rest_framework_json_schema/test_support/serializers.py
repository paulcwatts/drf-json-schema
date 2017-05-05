from copy import deepcopy

from rest_framework import serializers

from ..relations import JSONAPIRelationshipField
from ..schema import ResourceObject
from ..transforms import CamelCaseTransform


class BaseModel(object):
    @property
    def pk(self):
        return self.id

    # This is used to fake a Django model for the purposes
    # of RelatedField.use_pk_only_optimization. It just
    # needs to return the ID value for foreign keys.
    def serializable_value(self, field_name):
        try:
            value = getattr(self, field_name)
            return value.id
        except AttributeError:
            return getattr(self, field_name)


class Artist(BaseModel):
    def __init__(self, id, first_name, last_name):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name

    def update(self, id, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name


class Album(BaseModel):
    def __init__(self, id, album_name, artist):
        self.id = id
        self.album_name = album_name
        self.artist = artist

    @property
    def tracks(self):
        return [track for track in TRACKS if track.album.id == self.id]


class Track(BaseModel):
    def __init__(self, id, track_num, name, album):
        self.id = id
        self.track_num = track_num
        self.name = name
        self.album = album


INITIAL_ARTISTS = [
    Artist(0, 'Miles', 'Davis'),
    Artist(1, 'John', 'Coltrane'),
    Artist(2, 'Charles', 'Mingus'),
    Artist(3, 'Bill', 'Evans'),
    Artist(4, 'Max', 'Roach'),
    Artist(5, 'Sun', 'Ra')
]
ARTISTS = None

INITIAL_ALBUMS = [
    Album(0, 'A Love Supreme', INITIAL_ARTISTS[1]),
    Album(1, 'Birth of the Cool', INITIAL_ARTISTS[0]),
    Album(2, 'Space is the Place', INITIAL_ARTISTS[5]),
    Album(3, 'Unknown Artist', None)
]
ALBUMS = None

INITIAL_TRACKS = [
    Track(0, 1, 'Jeru', INITIAL_ALBUMS[1]),
    Track(1, 2, 'Moon Dreams', INITIAL_ALBUMS[1]),
    Track(2, 3, 'Venus de Milo', INITIAL_ALBUMS[1]),
    Track(3, 4, 'Deception', INITIAL_ALBUMS[1])
]
TRACKS = None


def get_artists():
    return ARTISTS


def get_albums():
    return ALBUMS


def get_tracks():
    return TRACKS


def reset_data():
    global ARTISTS
    global ALBUMS
    global TRACKS
    ARTISTS = deepcopy(INITIAL_ARTISTS)
    ALBUMS = deepcopy(INITIAL_ALBUMS)
    TRACKS = deepcopy(INITIAL_TRACKS)


reset_data()


class ArtistObject(ResourceObject):
    type = 'artist'
    attributes = ('first_name', 'last_name')
    transformer = CamelCaseTransform


class AlbumObject(ResourceObject):
    type = 'album'
    attributes = ('album_name',)
    relationships = ('artist', 'tracks')
    transformer = CamelCaseTransform


class TrackObject(ResourceObject):
    type = 'track'
    attributes = ('track_num', 'name')
    relationships = ('album',)
    transformer = CamelCaseTransform


class ArtistSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    first_name = serializers.CharField()
    last_name = serializers.CharField()

    schema = ArtistObject

    def create(self, validated_data):
        validated_data['id'] = len(get_artists())
        get_artists().append(Artist(**validated_data))
        return validated_data

    def update(self, instance, validated_data):
        instance.update(**validated_data)
        return instance


class TrackSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    track_num = serializers.IntegerField()
    name = serializers.CharField()
    album = JSONAPIRelationshipField(
        serializer='rest_framework_json_schema.test_support.serializers.AlbumSerializer',
        queryset=get_albums)

    schema = TrackObject


class AlbumSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    album_name = serializers.CharField()
    artist = JSONAPIRelationshipField(serializer=ArtistSerializer, queryset=get_artists)
    tracks = JSONAPIRelationshipField(serializer=TrackSerializer, many=True, queryset=get_tracks)

    schema = AlbumObject
