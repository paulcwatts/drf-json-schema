from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APISimpleTestCase, APIRequestFactory

from rest_framework_json_schema.test_support.serializers import (
    reset_data, get_artists, get_albums, get_tracks)
from rest_framework_json_schema.test_support.views import ArtistViewSet, AlbumViewSet


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPIParserTestCase(APISimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_list = ArtistViewSet.as_view({'post': 'create'})
        self.view_detail = ArtistViewSet.as_view({'put': 'update'})

    def tearDown(self):
        reset_data()

    def test_detail_attributes(self):
        """
        You can update primary data attributes.
        """
        request = self.factory.put(reverse('artist-detail', kwargs={'pk': 1}), {
            'data': {
                'id': '1',
                'type': 'artist',
                'attributes': {
                    'firstName': 'Art',
                    'lastName': 'Blakey'
                }
            }
        })
        response = self.view_detail(request, pk=1)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '1',
                'type': 'artist',
                'attributes': {
                    'firstName': 'Art',
                    'lastName': 'Blakey'
                }
            }
        })
        artist = get_artists().get(1)
        self.assertEqual(artist.id, 1)
        self.assertEqual(artist.first_name, 'Art')
        self.assertEqual(artist.last_name, 'Blakey')

    def test_list_attributes(self):
        """
        You can create using primary data attributes
        """
        request = self.factory.post(reverse('artist-list'), {
            'data': {
                'type': 'artist',
                'attributes': {
                    'firstName': 'Thelonious',
                    'lastName': 'Monk'
                }
            }
        })
        response = self.view_list(request)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '6',
                'type': 'artist',
                'attributes': {
                    'firstName': 'Thelonious',
                    'lastName': 'Monk'
                }
            }
        })
        artist = get_artists().get(6)
        self.assertEqual(artist.id, 6)
        self.assertEqual(artist.first_name, 'Thelonious')
        self.assertEqual(artist.last_name, 'Monk')

    def test_relationships(self):
        """
        You can parse relationships.
        """
        album_list = AlbumViewSet.as_view({'post': 'create'})
        artist = get_artists().get(0)
        track = get_tracks().get(0)
        request = self.factory.post(reverse('album-list'), {
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
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
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
        })
        album = get_albums()[4]
        self.assertEqual(album.album_name, 'On the Corner')
        self.assertEqual(album.artist.id, artist.id)
