from collections import OrderedDict
from typing import (
    Any,
    Optional,
    Dict,
    Sequence,
    Tuple,
    List,
    Callable,
    Union,
    Type,
    cast,
    Iterator,
    overload,
)

from django.urls import reverse
from rest_framework.request import Request

from .exceptions import TypeConflict, IncludeInvalid
from .transforms import NullTransform, Transform

# This is the type that can be specified by subclasses
RelOptType = Union[str, Tuple[str, "RelationshipObject"]]
# This is the normalized type we set in the constructor
RelType = Tuple[str, "RelationshipObject"]
ObjDataType = Dict[str, Any]
RenderResultType = Tuple[Dict[str, Any], List[Dict[str, Any]]]


class Context:
    """Collection of arguments needed for rendering/parsing."""

    def __init__(
        self,
        request: Request,
        include: Optional[Dict] = None,
        fields: Optional[Dict] = None,
    ) -> None:
        self.request = request
        self.include = include or {}
        self.fields = fields or {}


class BaseLinkedObject:
    links: Sequence[Tuple[str, "LinkObject"]] = ()
    meta: Optional[Dict] = None

    def render_links(self, data: ObjDataType, context: Context) -> OrderedDict:
        return OrderedDict(
            (link_name, link_obj.render(data, context.request))
            for (link_name, link_obj) in self.links
        )

    def render_meta(self, data: Any, context: Context) -> Optional[Dict]:
        """
        Render metadata.

        Implement this in your subclass if you have more complex meta information
        that depends on data or the request.
        """
        return self.meta


class ResourceObject(BaseLinkedObject):
    """
    Implement the base document resource object.

    http://jsonapi.org/format/#document-resource-objects
    """

    # REQUIRED members
    id: str = "id"
    type: str = "unknown"

    # OPTIONAL members
    attributes: Sequence[str] = ()
    relationships: Sequence[RelOptType] = ()
    transformer: Type[Transform] = NullTransform

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.transformed_names: Dict[str, str] = {}
        transformer = self.transformer()
        for name in self.attributes:
            self.transformed_names[name] = transformer.transform(name)

        # Normalize the relationships array to always be a tuple of (name, relobj)
        def _normalize_rel(rel: RelOptType) -> RelType:
            return (rel, RelationshipObject()) if isinstance(rel, str) else rel

        self.relationships = [_normalize_rel(rel) for rel in self.relationships]

        for (name, _rel) in self.relationships:
            self.transformed_names[name] = transformer.transform(name)

    def parse(self, data: ObjDataType, context: Context) -> Dict:
        """
        Parses a Resource Object representation into an internal representation.

        Verifies that the object is of the correct type.
        """
        type = data.get("type")
        if type != self.type:
            raise TypeConflict(
                "type %s is not the correct type for this resource" % type
            )
        result: OrderedDict = OrderedDict()
        id = data.get("id")
        if id:
            result["id"] = id
        attributes = data.get("attributes")
        if attributes:
            result.update(
                {
                    attr: attributes[self.transformed_names[attr]]
                    for attr in self.attributes
                    if self.transformed_names[attr] in attributes
                }
            )
        relationships = data.get("relationships")
        if relationships:
            result.update(
                {
                    name: cast(RelationshipObject, rel).parse(
                        relationships[self.transformed_names[name]], context
                    )
                    for (name, rel) in self.relationships
                    if self.transformed_names[name] in relationships
                }
            )
        return result

    def render(self, data: ObjDataType, context: Context) -> RenderResultType:
        """Renders data to a Resource Object representation."""
        result: Dict[str, Dict] = OrderedDict(  # type: ignore
            (("id", str(data[self.id])), ("type", self.type))
        )
        attributes = self.render_attributes(data, context)
        if attributes:
            result["attributes"] = attributes

        relationships, included = self.render_relationships(data, context)
        if relationships:
            result["relationships"] = relationships

        links = self.render_links(data, context)
        if links:
            result["links"] = links

        meta = self.render_meta(data, context)
        if meta:
            result["meta"] = meta
        return result, included

    def render_attributes(self, data: Dict, context: Context) -> ObjDataType:
        attributes = self.filter_by_fields(self.attributes, context.fields, lambda x: x)
        return OrderedDict(
            (self.transformed_names[attr], self.from_data(data, attr))
            for attr in attributes
            if attr in data
        )

    def render_relationships(self, data: Dict, context: Context) -> RenderResultType:
        relationships: Dict[str, Dict] = OrderedDict()
        included = []
        # Validate that all top-level include keys are actually relationships
        rel_keys = {rel[0] for rel in self.relationships}
        for key in context.include:
            if key not in rel_keys:
                raise IncludeInvalid("Invalid relationship to include: %s" % key)

        filtered = self.filter_by_fields(
            cast(Sequence[RelType], self.relationships), context.fields, lambda x: x[0]
        )
        # Filter by missing values in the data
        filtered = (rel for rel in filtered if rel[0] in data)
        for (name, rel) in filtered:
            relationship, rel_included = self.render_relationship(
                data, name, rel, context
            )
            relationships[self.transformed_names[name]] = relationship
            included.extend(rel_included)

        return relationships, included

    def render_relationship(
        self, data: Dict, rel_name: str, rel: "RelationshipObject", context: Context
    ) -> RenderResultType:
        # This relationship is included if rel_name is in the include paths.
        include_this = rel_name in context.include
        # Create a new context by going one level deeper into the include paths.
        rel_context = Context(
            context.request, context.include.get(rel_name, {}), context.fields
        )
        rel_data = self.from_data(data, rel_name)
        return rel.render(data, rel_data, rel_context, include_this)

    def from_data(self, data: Dict, attr: str) -> Any:
        # This is easy for now, but eventually we want to be able to specify
        # functions and the like
        return data[attr]

    @overload  # noqa: F811
    def filter_by_fields(
        self, names: Sequence[RelType], fields: Dict, name_fn: Callable[[RelType], str]
    ) -> Iterator[RelType]:
        ...

    @overload  # noqa: F811
    def filter_by_fields(
        self, names: Sequence[str], fields: Dict, name_fn: Callable[[str], str]
    ) -> Iterator[str]:
        ...

    def filter_by_fields(  # noqa: F811
        self, names: Sequence[Any], fields: Dict, name_fn: Callable[[Any], str]
    ) -> Iterator[Any]:
        """Filters the list of names by the list of fields."""
        if self.type not in fields:
            return iter(names)
        type_fields = fields[self.type]
        # This is essentially an intersection, but we preserve the order
        # of the attributes/relationships specified by the schema.
        return (
            name
            for name in names
            if self.transformed_names[name_fn(name)] in type_fields
        )


class ResourceIdObject(BaseLinkedObject):
    """http://jsonapi.org/format/#document-resource-identifier-objects"""

    id: Optional[str] = None
    type: str = "unknown"

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render(self, request: Request) -> Dict[str, Any]:
        result: Dict[str, Any] = OrderedDict(
            (("id", str(self.id)), ("type", self.type))
        )
        meta = self.render_meta(self, request)
        if meta:
            result["meta"] = meta
        return result

    def get_schema(self) -> ResourceObject:
        """
        Subclasses can override this with a mechanism to get the schema for a resource object.
        This is optional, but required for including resources.
        """
        raise IncludeInvalid()

    def get_data(self) -> Dict[str, Any]:
        """
        Subclasses can override this with a mechanism to get the rendered data for resource object.
        This is optional, but required for including resources.
        """
        raise IncludeInvalid()


class RelationshipObject(BaseLinkedObject):
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render_included(
        self, rel_data: "ResourceIdObject", context: Context
    ) -> List[Dict[str, Any]]:
        # This recursively calls the resource's schema to render the full object.
        schema = rel_data.get_schema()
        obj, included = schema.render(rel_data.get_data(), context)
        return [obj] + included

    def render(
        self,
        obj_data: ObjDataType,
        rel_data: ResourceIdObject,
        context: Context,
        include_this: bool,
    ) -> RenderResultType:
        result: ObjDataType = OrderedDict()
        included: List[ObjDataType] = []

        if not rel_data:
            # None or []
            result["data"] = rel_data
        elif isinstance(rel_data, ResourceIdObject):
            result["data"] = rel_data.render(context.request)
            if include_this:
                included.extend(self.render_included(rel_data, context))
        else:
            # Probably a list of resource objects
            if include_this:
                result["data"] = []
                for obj in rel_data:
                    result["data"].append(obj.render(context.request))
                    included.extend(self.render_included(obj, context))
            else:
                result["data"] = [obj.render(context.request) for obj in rel_data]

        links = self.render_links(obj_data, context)
        if links:
            result["links"] = links

        meta = self.render_meta(obj_data, context)
        if meta:
            result["meta"] = meta
        return result, included

    def parse(
        self, obj_data: ObjDataType, context: Context
    ) -> Union[str, List[str], None]:
        # Unless the Schema provides it, there's no way to verify the type
        # of the relationship. So we just look for the ID and propagate it.
        data = obj_data.get("data")
        if isinstance(data, list):
            return [obj["id"] for obj in data]
        elif isinstance(data, dict):
            return data["id"]
        return None


class LinkObject:
    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render(self, data: ObjDataType, request: Request) -> Any:
        raise NotImplementedError("Subclasses are required to implement this method.")


class UrlLink(LinkObject):
    absolute: bool = True
    view_name: Optional[str] = None
    # Mappings from values in data to the 'args' parameter to reverse()
    url_args: List[Any] = []
    # Mappings from values in data to the 'kwargs' parameter to reverse()
    url_kwargs: Dict[str, Any] = {}

    def render(self, data: ObjDataType, request: Request) -> Any:
        args = [data[arg] for arg in self.url_args]
        kwargs = {key: data[arg] for key, arg in self.url_kwargs.items()}
        link = reverse(self.view_name, args=args, kwargs=kwargs)
        if self.absolute:
            link = request.build_absolute_uri(link)
        return link
