import json

from django.urls import reverse
from rest_framework.test import APIRequestFactory

from tests.support.decorators import mark_urls
from tests.support.views import PaginateViewSet, NonJSONPaginateViewSet


@mark_urls
def test_pagination_limit_offset(factory: APIRequestFactory) -> None:
    """Pagination works according to spec."""
    list_url = reverse("page-list")
    request = factory.get(list_url, {"offset": 2, "limit": 2})
    view_list = PaginateViewSet.as_view({"get": "list"})

    response = view_list(request)
    response.render()
    assert response["Content-Type"] == "application/vnd.api+json"

    assert json.loads(response.content.decode()) == {
        "meta": {"count": 6},
        "links": {
            "page[next]": f"http://testserver{list_url}?limit=2&offset=4",
            "page[previous]": f"http://testserver{list_url}?limit=2",
        },
        "data": [
            {
                "id": "2",
                "type": "artist",
                "attributes": {"firstName": "Charles", "lastName": "Mingus"},
            },
            {
                "id": "3",
                "type": "artist",
                "attributes": {"firstName": "Bill", "lastName": "Evans"},
            },
        ],
    }


@mark_urls
def test_no_pagination_limit_offset(factory: APIRequestFactory) -> None:
    list_url = reverse("page-list")
    request = factory.get(list_url, {"offset": 2, "limit": 2})
    view_list = NonJSONPaginateViewSet.as_view({"get": "list"})
    response = view_list(request)
    response.render()
    # This really is misconfigured, it's mostly when someone has forgotten
    # to add a JSONAPI paginator to the View.
    assert response["Content-Type"] == "application/vnd.api+json"
    data = json.loads(response.content.decode())
    assert "meta" in data
    assert "data" in data["meta"]
