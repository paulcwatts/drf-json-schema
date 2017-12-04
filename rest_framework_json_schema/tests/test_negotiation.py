from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APISimpleTestCase, APIRequestFactory
from rest_framework_json_schema.negotiation import JSONAPIContentNegotiation

from rest_framework_json_schema.test_support.views import ArtistViewSet


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPINegotiationTestCase(APISimpleTestCase):
    maxDiff = None

    def test_accept_list(self):
        """
        The negotiator filters application/vnd.api+json with params, but not any non-vnd.api+json
        """
        negotiator = JSONAPIContentNegotiation()
        factory = APIRequestFactory()

        request = factory.get(reverse('artist-list'), HTTP_ACCEPT='application/vnd.api+json')
        accept_list = negotiator.get_accept_list(request)
        self.assertEqual(accept_list, ['application/vnd.api+json'])

        accept = 'text/html,application/vnd.api+json;indent=4,application/xml;q=0.9,*/*;q=0.8'
        request = factory.get(reverse('artist-list'), HTTP_ACCEPT=accept)
        accept_list = negotiator.get_accept_list(request)
        self.assertEqual(accept_list, ['text/html', 'application/xml;q=0.9', '*/*;q=0.8'])

    def test_media_params(self):
        """
        Servers MUST respond with a 406 Not Acceptable status code if a request's Accept header
        contains the JSON API media type and all instances of that media type are
        modified with media type parameters.
        """
        factory = APIRequestFactory()
        view_list = ArtistViewSet.as_view({'get': 'list'})

        request = factory.get(reverse('artist-list'),
                              HTTP_ACCEPT='application/vnd.api+json')
        response = view_list(request)
        # Acceptable
        self.assertEqual(response.status_code, 200)

        request = factory.get(reverse('artist-list'),
                              HTTP_ACCEPT='application/vnd.api+json; indent=4')
        response = view_list(request)
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.data, {
            'detail': 'Could not satisfy the request Accept header.'
        })
