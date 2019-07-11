from collections import OrderedDict

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList

from .helpers import JSONReturnList


class JSONAPILimitOffsetPagination(LimitOffsetPagination):
    def get_paginated_response(self, data: ReturnList) -> Response:
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
