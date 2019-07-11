"""Renderers are used to serialize a response into specific media types."""

import re
from collections import OrderedDict
from typing import Any, Dict, Optional, Mapping, List, Union, Tuple, Type

from rest_framework.renderers import JSONRenderer

from .exceptions import NoSchema
from .schema import Context, ResourceObject, ObjDataType, RenderResultType
from .utils import parse_include

RX_FIELDS = re.compile(r"^fields\[([a-zA-Z0-9\-_]+)\]$")


class JSONAPIRenderer(JSONRenderer):
    """Renderer which serializes to JSON API."""

    media_type: str = "application/vnd.api+json"
    format: str = "vnd.api+json"
    # You can specify top-level items here.
    meta: Optional[Dict[str, Any]] = None
    jsonapi: Optional[Any] = None

    def render_obj(
        self,
        obj: ObjDataType,
        schema: ResourceObject,
        renderer_context: Mapping[str, Any],
        context: Context,
    ) -> RenderResultType:
        """Render a single resource object as primary data."""
        return schema.render(obj, context)

    def render_list(
        self,
        obj_list: List[ObjDataType],
        schema: ResourceObject,
        renderer_context: Mapping[str, Any],
        context: Context,
    ) -> Tuple[Union[ObjDataType, List[ObjDataType]], List[ObjDataType]]:
        """
        Render a list a resource objects as primary data.

        In addition, render include resources if they are requested.
        """
        primary = []
        included = []
        for obj in obj_list:
            obj, inc = self.render_obj(obj, schema, renderer_context, context)
            primary.append(obj)
            included.extend(inc)

        return primary, included

    def render_data(
        self,
        data: Union[Dict, List],
        renderer_context: Mapping[str, Any],
        include: Dict,
    ) -> Tuple[Union[ObjDataType, List[ObjDataType], None], List[ObjDataType]]:
        """Render primary data and included resources."""
        schema = self.get_schema(data, renderer_context)
        assert schema, "Unable to get schema class"
        fields = self.get_fields(renderer_context)
        context = Context(renderer_context.get("request", None), include, fields)

        if isinstance(data, dict):
            return self.render_obj(data, schema(), renderer_context, context)

        elif isinstance(data, list):
            return self.render_list(data, schema(), renderer_context, context)
        return None, []

    def render_exception(self, data: Any, renderer_context: Mapping[str, Any]) -> Any:
        """Render an exception result."""
        return [data]

    def is_exception(self, data: Any, renderer_context: Mapping[str, Any]) -> bool:
        """Return whether we're trying to render an exception."""
        return renderer_context["response"].exception

    def get_schema(
        self, data: Any, renderer_context: Mapping[str, Any]
    ) -> Type[ResourceObject]:
        """Override this if you have a different way to get the schema."""
        try:
            serializer = data.serializer
        except AttributeError:
            raise NoSchema()

        if not getattr(serializer, "many", False):
            return serializer.schema
        else:
            return serializer.child.schema

    def get_include(self, renderer_context: Mapping[str, Any]) -> Dict[str, Dict]:
        """Return the parsed include parameter, if it exists."""
        request = renderer_context.get("request", None)
        if request:
            return parse_include(request.query_params.get("include", ""))
        else:
            return {}

    def get_fields(self, renderer_context: Mapping[str, Any]) -> Dict[str, str]:
        """Return the parsed fields parameters, if any exist."""
        request = renderer_context.get("request", None)
        fields = {}
        if request:
            for key, value in request.query_params.items():
                m = RX_FIELDS.match(key)
                if m:
                    fields[m.group(1)] = value.split(",")
        return fields

    def render(
        self,
        data: Any,
        media_type: Optional[str] = None,
        renderer_context: Optional[Mapping[str, Any]] = None,
    ) -> bytes:
        """Render `data` into JSON API, returning a bytestring."""

        if data is None:
            return bytes()

        if not renderer_context:
            return bytes()

        to_include = self.get_include(renderer_context)
        rendered: Dict[str, Any] = OrderedDict()
        if self.jsonapi:
            rendered["jsonapi"] = self.jsonapi

        meta: Dict = {}
        links: Dict[str, Any] = {}

        if self.meta:
            meta.update(self.meta)

        if self.is_exception(data, renderer_context):
            rendered["errors"] = self.render_exception(data, renderer_context)
        else:
            try:
                rendered_data, included = self.render_data(
                    data, renderer_context, to_include
                )
                if rendered_data is not None:
                    rendered["data"] = rendered_data
                if included:
                    rendered["included"] = included
            except NoSchema:
                # Because we don't know the type of this data, we can't include it as
                # primary data.
                meta["data"] = data

        data_meta = getattr(data, "meta", None)
        if data_meta:
            meta.update(data_meta)
        data_links = getattr(data, "links", None)
        if data_links:
            links.update(data_links)

        if meta:
            rendered["meta"] = meta
        if links:
            rendered["links"] = links

        return super().render(rendered, media_type, renderer_context)


class JSONAPITestRenderer(JSONRenderer):
    """
    Render test JSON.

    This is a simple wrapper of the original JSONRenderer that supports
    the JSON media type. This is used to specify fully-rendered JSON API
    requests in test code, but still be able to fully test parsers.
    """

    media_type: str = "application/vnd.api+json"
    format: str = "vnd.api+json"
