from collections import OrderedDict

from rest_framework.renderers import JSONRenderer


class JSONAPIRenderer(JSONRenderer):
    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'
    # You can specify top-level items here.
    meta = None
    jsonapi = None

    def render_obj(self, obj, schema, renderer_context):
        return schema.render(obj, renderer_context.get('request', None))

    def render_list(self, obj_list, schema, renderer_context):
        return [self.render_obj(obj, schema, renderer_context) for obj in obj_list]

    def render_data(self, data, schema, renderer_context):
        if isinstance(data, dict):
            return self.render_obj(data, schema(), renderer_context)

        elif isinstance(data, list):
            return self.render_list(data, schema(), renderer_context)

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

    def render(self, data, media_type=None, renderer_context=None):
        if data is None:
            return bytes()

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
            schema = self.get_schema(data, renderer_context)
            assert schema, 'Unable to get schema class'

            rendered['data'] = self.render_data(data, schema, renderer_context)

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
