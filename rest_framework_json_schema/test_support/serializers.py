from copy import deepcopy

from rest_framework import serializers

from ..relations import JSONAPIRelationshipField
from ..schema import ResourceObject
from ..transforms import CamelCaseTransform


class Artist(object):
    def __init__(self, id, first_name, last_name):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name

    def update(self, id, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    @property
    def pk(self):
        return self.id


class Album(object):
    def __init__(self, id, album_name, artist):
        self.id = id
        self.album_name = album_name
        self.artist = artist

    @property
    def pk(self):
        return self.id


INITIAL_ARTISTS = [
    Artist(0, 'Miles', 'Davis'),
    Artist(1, 'John', 'Coltrane'),
    Artist(2, 'Charles', 'Mingus'),
    Artist(3, 'Bill', 'Evans'),
    Artist(4, 'Max', 'Roach'),
    Artist(4, 'Sun', 'Ra')
]
ARTISTS = None

INITIAL_ALBUMS = [
    Album(0, 'A Love Supreme', INITIAL_ARTISTS[1]),
    Album(1, 'Birth of the Cool', INITIAL_ARTISTS[0]),
    Album(2, 'Space is the Place', INITIAL_ARTISTS[5]),
    Album(3, 'Unknown Artist', None)
]
ALBUMS = None


def get_artists():
    return ARTISTS


def get_albums():
    return ALBUMS


def reset_data():
    global ARTISTS
    global ALBUMS
    ARTISTS = deepcopy(INITIAL_ARTISTS)
    ALBUMS = deepcopy(INITIAL_ALBUMS)


reset_data()


class ArtistObject(ResourceObject):
    type = 'artist'
    attributes = ('first_name', 'last_name')
    transformer = CamelCaseTransform


class AlbumObject(ResourceObject):
    type = 'album'
    attributes = ('album_name',)
    relationships = ('artist',)
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


class AlbumSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    album_name = serializers.CharField()
    artist = JSONAPIRelationshipField(serializer=ArtistSerializer, queryset=get_artists)

    schema = AlbumObject
