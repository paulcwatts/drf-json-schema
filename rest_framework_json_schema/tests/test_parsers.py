from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework.test import APISimpleTestCase, APIRequestFactory

from rest_framework_json_schema.test_support.serializers import reset_data, get_artists
from rest_framework_json_schema.test_support.views import ArtistViewSet


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
        artist = get_artists()[1]
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
        artist = get_artists()[6]
        self.assertEqual(artist.id, 6)
        self.assertEqual(artist.first_name, 'Thelonious')
        self.assertEqual(artist.last_name, 'Monk')
