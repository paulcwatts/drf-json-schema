"""Pagination serializers determine the structure for paginated responses."""

from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList

from .helpers import JSONReturnList


class JSONAPILimitOffsetPagination(LimitOffsetPagination):
    """Implement JSON API limit/offset pagination."""

    def get_paginated_response(self, data: ReturnList) -> Response:
        """
        Return the paginated response.

        Place the links under the correct location to be used by the
        JSONAPIRenderer to include in the output payload.

        https://jsonapi.org/format/#fetching-pagination
        """
        return Response(
            JSONReturnList(
                data,
                serializer=data.serializer,
                links=OrderedDict(
                    (
                        ("page[next]", self.get_next_link()),
                        ("page[previous]", self.get_previous_link()),
                    )
                ),
                meta=OrderedDict((("count", self.count),)),
            )
        )
