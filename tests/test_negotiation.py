from django.urls import reverse
from rest_framework.test import APIRequestFactory

from rest_framework_json_schema.negotiation import JSONAPIContentNegotiation
from tests.support.decorators import mark_urls
from tests.support.views import ArtistViewSet


@mark_urls
def test_accept_list(factory: APIRequestFactory) -> None:
    """The negotiator filters application/vnd.api+json with params, but not any non-vnd.api+json"""
    negotiator = JSONAPIContentNegotiation()

    request = factory.get(
        reverse("artist-list"), HTTP_ACCEPT="application/vnd.api+json"
    )
    accept_list = negotiator.get_accept_list(request)
    assert accept_list == ["application/vnd.api+json"]

    accept = (
        "text/html,application/vnd.api+json;indent=4,application/xml;q=0.9,*/*;q=0.8"
    )
    request = factory.get(reverse("artist-list"), HTTP_ACCEPT=accept)
    accept_list = negotiator.get_accept_list(request)
    assert accept_list == ["text/html", "application/xml;q=0.9", "*/*;q=0.8"]


@mark_urls
def test_media_params(factory: APIRequestFactory) -> None:
    """
    Support correct media params.

    Servers MUST respond with a 406 Not Acceptable status code if a request's Accept header
    contains the JSON API media type and all instances of that media type are
    modified with media type parameters.
    """
    view_list = ArtistViewSet.as_view({"get": "list"})

    request = factory.get(
        reverse("artist-list"), HTTP_ACCEPT="application/vnd.api+json"
    )
    response = view_list(request)
    # Acceptable
    assert response.status_code == 200

    request = factory.get(
        reverse("artist-list"), HTTP_ACCEPT="application/vnd.api+json; indent=4"
    )
    response = view_list(request)
    assert response.status_code == 406
    assert response.data == {"detail": "Could not satisfy the request Accept header."}
