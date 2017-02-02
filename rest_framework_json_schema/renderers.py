from collections import OrderedDict

from rest_framework.renderers import JSONRenderer

from .utils import parse_include


class JSONAPIRenderer(JSONRenderer):
    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'
    # You can specify top-level items here.
    meta = None
    jsonapi = None

    def render_obj(self, obj, schema, renderer_context, include):
        return schema.render(obj, renderer_context.get('request', None), include)

    def render_list(self, obj_list, schema, renderer_context, include):
        primary = []
        included = []
        for obj in obj_list:
            obj, inc = self.render_obj(obj, schema, renderer_context, include)
            primary.append(obj)
            included.extend(inc)

        return primary, included

    def render_data(self, data, renderer_context, include):
        schema = self.get_schema(data, renderer_context)
        assert schema, 'Unable to get schema class'

        if isinstance(data, dict):
            return self.render_obj(data, schema(), renderer_context, include)

        elif isinstance(data, list):
            return self.render_list(data, schema(), renderer_context, include)

    def render_exception(self, data, renderer_context):
        return [data]

    def is_exception(self, data, renderer_context):
        """
        Returns whether we're trying to render an exception.
        """
        return renderer_context['response'].exception

    def get_schema(self, data, renderer_context):
        """
        Override this if you have a different way to get the schema.
        """
        serializer = data.serializer
        if not getattr(serializer, 'many', False):
            return getattr(serializer, 'schema')
        else:
            return getattr(serializer.child, 'schema')

    def get_include(self, renderer_context):
        request = renderer_context.get('request', None)
        if request:
            return parse_include(request.query_params.get('include', ''))
        else:
            return {}

    def render(self, data, media_type=None, renderer_context=None):
        if data is None:
            return bytes()

        to_include = self.get_include(renderer_context)
        rendered = OrderedDict()
        if self.jsonapi:
            rendered['jsonapi'] = self.jsonapi

        meta = {}
        links = {}

        if self.meta:
            meta.update(self.meta)

        if self.is_exception(data, renderer_context):
            rendered['errors'] = self.render_exception(data, renderer_context)
        else:
            rendered_data, included = self.render_data(data, renderer_context, to_include)
            if rendered_data is not None:
                rendered['data'] = rendered_data
            if included:
                rendered['included'] = included

        data_meta = getattr(data, 'meta', None)
        if data_meta:
            meta.update(data_meta)
        data_links = getattr(data, 'links', None)
        if data_links:
            links.update(data_links)

        if meta:
            rendered['meta'] = meta
        if links:
            rendered['links'] = links

        return super(JSONAPIRenderer, self).render(rendered, media_type, renderer_context)


class JSONAPITestRenderer(JSONRenderer):
    """
    This is a simple wrapper of the original JSONRenderer that supports
    the JSON media type. This is used to specify fully-rendered JSON API
    requests in test code, but still be able to fully test parsers.
    """
    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'
