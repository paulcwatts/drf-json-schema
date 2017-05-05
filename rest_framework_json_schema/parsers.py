from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, status
from rest_framework.parsers import JSONParser

from .exceptions import TypeConflict
from .renderers import JSONAPIRenderer
from .schema import Context


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Invalid resource type for endpoint.')
    default_code = 'conflict'


class JSONAPIParser(JSONParser):
    media_type = 'application/vnd.api+json'
    renderer_class = JSONAPIRenderer

    def get_schema(self, parser_context):
        """
        Override this if this isn't the way you back to your schema.
        """
        return parser_context['view'].serializer_class.schema

    def parse(self, stream, media_type=None, parser_context=None):
        toplevel = super(JSONAPIParser, self).parse(stream, media_type, parser_context)

        schema = self.get_schema(parser_context)
        data = toplevel.get('data')
        if not data:
            raise exceptions.ValidationError('No primary data.')

        try:
            parsed = schema().parse(data, Context(parser_context.get('request', None)))
        except TypeConflict as e:
            raise Conflict(str(e))

        return parsed
