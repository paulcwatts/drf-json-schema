import json

from django.urls import reverse
from rest_framework.test import APIRequestFactory

from tests.support.decorators import mark_urls
from tests.support.serializers import (
    get_artists, get_albums, get_tracks)
from tests.support.views import ArtistViewSet, AlbumViewSet


@mark_urls
def test_detail_attributes(factory: APIRequestFactory) -> None:
    """You can update primary data attributes."""
    request = factory.put(reverse('artist-detail', kwargs={'pk': 1}), {
        'data': {
            'id': '1',
            'type': 'artist',
            'attributes': {
                'firstName': 'Art',
                'lastName': 'Blakey'
            }
        }
    })
    view_detail = ArtistViewSet.as_view({'put': 'update'})
    response = view_detail(request, pk=1)
    response.render()
    assert response['Content-Type'] == 'application/vnd.api+json'
    assert json.loads(response.content) == {
        'data': {
            'id': '1',
            'type': 'artist',
            'attributes': {
                'firstName': 'Art',
                'lastName': 'Blakey'
            }
        }
    }
    artist = get_artists().get(1)
    assert artist.id == 1
    assert artist.first_name == 'Art'
    assert artist.last_name == 'Blakey'


@mark_urls
def test_list_attributes(factory: APIRequestFactory) -> None:
    """You can create using primary data attributes."""
    request = factory.post(reverse('artist-list'), {
        'data': {
            'type': 'artist',
            'attributes': {
                'firstName': 'Thelonious',
                'lastName': 'Monk'
            }
        }
    })
    view_list = ArtistViewSet.as_view({'post': 'create'})
    response = view_list(request)
    response.render()
    assert response['Content-Type'] == 'application/vnd.api+json'
    assert json.loads(response.content) == {
        'data': {
            'id': '6',
            'type': 'artist',
            'attributes': {
                'firstName': 'Thelonious',
                'lastName': 'Monk'
            }
        }
    }
    artist = get_artists().get(6)
    assert artist.id == 6
    assert artist.first_name == 'Thelonious'
    assert artist.last_name == 'Monk'


@mark_urls
def test_parse_relationships(factory: APIRequestFactory) -> None:
    """You can parse relationships."""
    album_list = AlbumViewSet.as_view({'post': 'create'})
    artist = get_artists().get(0)
    track = get_tracks().get(0)
    request = factory.post(reverse('album-list'), {
        'data': {
            'type': 'album',
            'attributes': {
                'albumName': 'On the Corner'
            },
            'relationships': {
                'artist': {
                    'data': {
                        'id': artist.id,
                        'type': 'artist'
                    }
                },
                'tracks': {
                    'data': [{
                        'id': track.id,
                        'type': 'track'
                    }]
                }
            }
        }
    })
    response = album_list(request)
    response.render()
    assert response['Content-Type'] == 'application/vnd.api+json'
    assert json.loads(response.content) == {
        'data': {
            'id': '4',
            'type': 'album',
            'attributes': {
                'albumName': 'On the Corner'
            },
            'relationships': {
                'artist': {
                    'data': {
                        'id': str(artist.id),
                        'type': 'artist'
                    }
                },
                'tracks': {
                    'data': [
                        {'id': '0', 'type': 'track'}
                    ]
                }
            }
        }
    }
    album = get_albums()[4]
    assert album.album_name == 'On the Corner'
    assert album.artist.id == artist.id
