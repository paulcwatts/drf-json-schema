import json

from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework.test import APISimpleTestCase, APIRequestFactory

from rest_framework_json_schema.test_support.serializers import reset_data
from rest_framework_json_schema.test_support.views import ArtistViewSet, AlbumViewSet


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPIAttributesRendererTestCase(APISimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_list = ArtistViewSet.as_view({'get': 'list'})
        self.view_detail = ArtistViewSet.as_view({'get': 'retrieve'})
        reset_data()

    def test_detail_attributes(self):
        """
        You can render primary data object attributes
        """
        request = self.factory.get(reverse('artist-detail', kwargs={'pk': 1}))
        response = self.view_detail(request, pk=1)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '1',
                'type': 'artist',
                'attributes': {
                    'firstName': 'John',
                    'lastName': 'Coltrane'
                }
            }
        })

    def test_list_attributes(self):
        """
        You can render primary data list attributes
        """
        request = self.factory.get(reverse('artist-list'))
        response = self.view_list(request)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')

        data = json.loads(response.content.decode())['data']
        self.assertEqual(data[:3], [
            {
                'id': '0',
                'type': 'artist',
                'attributes': {'firstName': 'Miles', 'lastName': 'Davis'}
            },
            {
                'id': '1',
                'type': 'artist',
                'attributes': {'firstName': 'John', 'lastName': 'Coltrane'}
            },
            {
                'id': '2',
                'type': 'artist',
                'attributes': {'firstName': 'Charles', 'lastName': 'Mingus'}
            }
        ])

    def test_exception(self):
        """
        The renderer handles thrown exceptions.
        """
        request = self.factory.get(reverse('artist-detail', kwargs={'pk': 8}))
        response = self.view_detail(request, pk=8)
        response.render()
        self.assertJSONEqual(response.content.decode(), {
            'errors': [
                {
                    'detail': 'Not found.'
                }
            ]
        })


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPIRelationshipsRendererTestCase(APISimpleTestCase):
    maxDiff = None

    def setUp(self):
        self.factory = APIRequestFactory()
        # self.view_list = AlbumViewSet.as_view({'get': 'list'})
        self.view_detail = AlbumViewSet.as_view({'get': 'retrieve'})
        reset_data()

    def test_to_one_empty(self):
        """
        You can render an empty to-one relationship
        """
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 3}))
        response = self.view_detail(request, pk=3)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '3',
                'type': 'album',
                'attributes': {
                    'albumName': 'Unknown Artist'
                },
                'relationships': {
                    'artist': {
                        'data': None
                    }
                }
            }
        })

    def test_to_one_non_empty(self):
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 0}))
        response = self.view_detail(request, pk=0)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '0',
                'type': 'album',
                'attributes': {
                    'albumName': 'A Love Supreme'
                },
                'relationships': {
                    'artist': {
                        'data': {'id': '1', 'type': 'artist'}
                    }
                }
            }
        })

    # TODO: to-one included

    # TODO: to-many empty
    # TODO: to-many filled
    # TODO: included linkages
