from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.utils.mediatypes import _MediaType


class JSONAPIContentNegotiation(DefaultContentNegotiation):
    """
    This implements the following two MUSTs in the JSON API

    Servers MUST respond with a 415 Unsupported Media Type status code if a
    request specifies the header Content-Type: application/vnd.api+json
    with any media type parameters.

    Servers MUST respond with a 406 Not Acceptable status code if a request's
    Accept header contains the JSON API media type and all instances of that
    media type are modified with media type parameters.
    """
    def get_accept_list(self, request):
        """
        This filters out any JSON API specification that includes media parameters.
        """
        accept_list = super(JSONAPIContentNegotiation, self).get_accept_list(request)
        jsonapi = _MediaType('application/vnd.api+json')

        def jsonapi_no_params(media_type_str):
            media_type = _MediaType(media_type_str)
            return jsonapi.match(media_type) and not media_type.params

        return [accept for accept in accept_list if jsonapi_no_params(accept)]
