from collections import OrderedDict
from django.core.urlresolvers import reverse

from .exceptions import TypeConflict
from .transforms import NullTransform


class BaseLinkedObject(object):
    def render_links(self, data, request):
        return OrderedDict(
            (link_name, link_obj.render(data, request)) for (link_name, link_obj) in self.links
        )

    def render_meta(self, data, request):
        """
        Implement this in your subclass if you have more complex meta information
        that depends on data or the request.
        """
        return self.meta


class ResourceObject(BaseLinkedObject):
    """
    http://jsonapi.org/format/#document-resource-objects
    """
    # REQUIRED members
    id = 'id'
    type = 'unknown'

    # OPTIONAL members
    attributes = ()
    relationships = ()
    links = ()
    meta = None

    transformer = NullTransform

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.transformed_names = {}
        transformer = self.transformer()
        for name in self.attributes:
            self.transformed_names[name] = transformer.transform(name)

        # Normalize the relationships array to always be a tuple of (name, relobj)
        def _normalize_rel(rel):
            return (rel, RelationshipObject()) if isinstance(rel, str) else rel
        self.relationships = [_normalize_rel(rel) for rel in self.relationships]

        for (name, rel) in self.relationships:
            self.transformed_names[name] = transformer.transform(name)

    def parse(self, data, request):
        """
        Parses a Resource Object representation into an internal representation.
        Verifies that the object is of the correct type.
        """
        type = data.get('type')
        if type != self.type:
            raise TypeConflict('type %s is not the correct type for this resource' % type)
        result = OrderedDict()
        id = data.get('id')
        if id:
            result['id'] = id
        attributes = data.get('attributes')
        if attributes:
            result.update({
                attr: attributes[self.transformed_names[attr]]
                for attr in self.attributes if self.transformed_names[attr] in attributes
            })
        return result

    def render(self, data, request):
        """
        Renders data to a Resource Object representation.
        """
        result = OrderedDict((
            ('id', str(data[self.id])),
            ('type', self.type)
        ))
        attributes = self.render_attributes(data, request)
        if attributes:
            result['attributes'] = attributes

        relationships = self.render_relationships(data, request)
        if relationships:
            result['relationships'] = relationships

        links = self.render_links(data, request)
        if links:
            result['links'] = links

        meta = self.render_meta(data, request)
        if meta:
            result['meta'] = meta
        return result

    def render_attributes(self, data, request):
        return OrderedDict(
            (self.transformed_names[attr], self.from_data(data, attr)) for attr in self.attributes
        )

    def render_relationships(self, data, request):
        return OrderedDict(
            (self.transformed_names[name],
             self.render_relationship(data, name, rel, request)) for (name, rel) in self.relationships
        )

    def render_relationship(self, data, rel_name, rel, request):
        rel_data = self.from_data(data, rel_name)
        return rel.render(data, rel_data, request)

    def from_data(self, data, attr):
        # This is easy for now, but eventually we want to be able to specify
        # functions and the like
        return data[attr]


# TODO: All of this might be too complex for our ultimate goal.
# Simplify when we implement parsing and included resource
#
class ResourceIdObject(BaseLinkedObject):
    """
    http://jsonapi.org/format/#document-resource-identifier-objects
    """
    id = None
    type = 'unknown'
    meta = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render(self, request):
        result = OrderedDict((
            ('id', str(self.id)),
            ('type', self.type)
        ))
        meta = self.render_meta(self, request)
        if meta:
            result['meta'] = meta
        return result


class RelationshipObject(BaseLinkedObject):
    links = ()
    meta = None

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render(self, obj_data, rel_data, request):
        result = OrderedDict()
        if not rel_data:
            # None or []
            result['data'] = rel_data
        elif isinstance(rel_data, ResourceIdObject):
            result['data'] = rel_data.render(request)
        else:
            # Probably a list of resource objects
            result['data'] = [obj.render(request) for obj in rel_data]

        links = self.render_links(obj_data, request)
        if links:
            result['links'] = links

        meta = self.render_meta(obj_data, request)
        if meta:
            result['meta'] = meta
        return result


class LinkObject(object):
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def render(self, data, request):
        raise NotImplementedError('Subclasses are required to implement this method.')


class UrlLink(LinkObject):
    absolute = True
    view_name = None
    # Mappings from values in data to the 'args' parameter to reverse()
    url_args = []
    # Mappings from values in data to the 'kwargs' parameter to reverse()
    url_kwargs = {}

    def render(self, data, request):
        args = [data[arg] for arg in self.url_args]
        kwargs = {key: data[arg] for key, arg in self.url_kwargs.items()}
        link = reverse(self.view_name, args=args, kwargs=kwargs)
        if self.absolute:
            link = request.build_absolute_uri(link)
        return link
