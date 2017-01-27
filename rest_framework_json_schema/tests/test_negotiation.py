from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework.test import APISimpleTestCase, APIRequestFactory

from rest_framework_json_schema.test_support.views import ArtistViewSet


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPINegotiationTestCase(APISimpleTestCase):
    def test_media_params(self):
        """
        Servers MUST respond with a 406 Not Acceptable status code if a request's Accept header
        contains the JSON API media type and all instances of that media type are
        modified with media type parameters.
        """
        factory = APIRequestFactory()
        view_list = ArtistViewSet.as_view({'get': 'list'})

        request = factory.get(reverse('artist-list'), HTTP_ACCEPT='application/vnd.api+json')
        response = view_list(request)
        # Acceptable
        self.assertEqual(response.status_code, 200)

        request = factory.get(reverse('artist-list'), HTTP_ACCEPT='application/vnd.api+json; indent=4')
        response = view_list(request)
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.data, {
            'detail': 'Could not satisfy the request Accept header.'
        })

    # TODO: Servers MUST respond with a 415 Unsupported Media Type status code
    # if a request specifies the header Content-Type: application/vnd.api+json with any media type parameters.
