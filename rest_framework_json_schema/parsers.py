"""Parsers are used to parse the content of incoming HTTP requests."""

from typing import IO, Any, Optional, Mapping, Dict, Type

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.parsers import JSONParser

from .exceptions import TypeConflict
from .renderers import JSONAPIRenderer
from .schema import Context, ResourceObject


class Conflict(exceptions.APIException):
    """
    Status code for a JSON API resource conflict.

    https://jsonapi.org/format/#crud-creating-responses-409
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Invalid resource type for endpoint.")
    default_code = "conflict"


class JSONAPIParser(JSONParser):
    """Parses JSON API-serialized data."""

    media_type = "application/vnd.api+json"
    renderer_class = JSONAPIRenderer

    def get_schema(self, parser_context: Mapping[str, Any]) -> Type[ResourceObject]:
        """Override this if this isn't the way you back to your schema."""
        return parser_context["view"].serializer_class.schema

    def parse(
        self,
        stream: IO[Any],
        media_type: Optional[str] = None,
        parser_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Given a stream to read from, return the parsed representation."""

        toplevel = super().parse(stream, media_type, parser_context)
        if not parser_context:
            raise ValueError("Parser context required")

        schema = self.get_schema(parser_context)
        data = toplevel.get("data")
        if not data:
            raise exceptions.ValidationError("No primary data.")

        try:
            parsed = schema().parse(data, Context(parser_context.get("request", None)))
        except TypeConflict as e:
            raise Conflict(str(e))

        return parsed
