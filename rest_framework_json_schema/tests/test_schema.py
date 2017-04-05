from collections import OrderedDict
from django.test import SimpleTestCase, override_settings

from rest_framework.test import APIRequestFactory

from rest_framework_json_schema.exceptions import TypeConflict, IncludeInvalid
from rest_framework_json_schema.schema import (ResourceObject, RelationshipObject,
                                               ResourceIdObject, LinkObject, UrlLink)
from rest_framework_json_schema.transforms import CamelCaseTransform
from rest_framework_json_schema.utils import parse_include


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class ResourceObjectTest(SimpleTestCase):
    maxDiff = None

    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')

    def test_default(self):
        # With no attributes, nothing is included, just the ID.
        primary, included = ResourceObject().render({
            'id': '123',
            'attribute': 'ignored'
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'unknown')
        )))
        self.assertEqual(included, [])

    def test_constructor(self):
        """
        You can specify the schema using the constructor.
        """
        obj = ResourceObject(id='user_id', type='users', attributes=('name',))
        primary, included = obj.render({
            'user_id': '123',
            'name': 'John'
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'users'),
            ('attributes', OrderedDict((('name', 'John'),)))
        )))
        self.assertEqual(included, [])

    def test_subclass(self):
        """
        You can use a subclass to specify schema information.
        """
        class TestObject(ResourceObject):
            id = 'user_id'
            type = 'users'
            attributes = ('name',)

        primary, included = TestObject().render({
            'user_id': '123',
            'name': 'John'
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'users'),
            ('attributes', OrderedDict((('name', 'John'),)))
        )))
        self.assertEqual(included, [])

    def test_links(self):
        """
        You can specify links which are methods on the object.
        """
        class ObjectLink(LinkObject):
            def render(self, data, request):
                return {
                    'href': '/users/%s' % data['id'],
                    'meta': {
                        'something': 'hello'
                    }
                }

        class TestObject(ResourceObject):
            type = 'artists'
            links = (
                ('self', UrlLink(view_name='artist-detail',
                                 url_kwargs={'pk': 'id'})),
                ('relative', UrlLink(view_name='artist-detail',
                                     url_kwargs={'pk': 'id'},
                                     absolute=False)),
                ('object', ObjectLink())
            )

        primary, included = TestObject().render({'id': '123'}, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'artists'),
            ('links', OrderedDict((
                ('self', 'http://testserver/api/artist/123/'),
                ('relative', '/api/artist/123/'),
                ('object', {
                    'href': '/users/123',
                    'meta': {'something': 'hello'}
                }))))
        )))
        self.assertEqual(included, [])

    def test_meta(self):
        """
        An optional meta object is rendered
        """
        obj = ResourceObject(type='users', meta={'foo': 'bar'})
        primary, included = obj.render({'id': '123'}, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'users'),
            ('meta', {'foo': 'bar'}))
        ))
        self.assertEqual(included, [])

    def test_render_relationships(self):
        """
        This tests that relationships can be rendered with their associated metadata.
        """
        class AlbumObject(ResourceObject):
            type = 'album'
            relationships = ('artist',)

        # Empty to-one relationship: relationship is 'None'
        # Empty to-many relationship: relationship is '[]'
        # Single relationship: a ResourceIdObject
        # To-Many: an array of ResourceIdObjects
        obj = AlbumObject()

        primary, included = obj.render({'id': '123', 'artist': None}, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'album'),
            ('relationships', OrderedDict((
                ('artist', OrderedDict((('data', None),))),
            )))
        )))
        self.assertEqual(included, [])

        primary, included = obj.render({'id': '123', 'artist': []}, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'album'),
            ('relationships', OrderedDict((
                ('artist', OrderedDict((('data', []),))),
            )))
        )))
        self.assertEqual(included, [])

        primary, included = obj.render({
            'id': '123',
            'artist': ResourceIdObject(id=5, type='artist')
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'album'),
            ('relationships', OrderedDict((
                ('artist', OrderedDict((
                    ('data', OrderedDict((('id', '5'), ('type', 'artist')))),
                ))),
            )))
        )))
        self.assertEqual(included, [])

        primary, included = obj.render({
            'id': '123',
            'artist': [
                ResourceIdObject(id=5, type='artist'),
                ResourceIdObject(id=6, type='artist')
            ]
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'album'),
            ('relationships', OrderedDict((
                ('artist', OrderedDict((
                    ('data', [
                        OrderedDict((('id', '5'), ('type', 'artist'))),
                        OrderedDict((('id', '6'), ('type', 'artist')))
                    ]),
                ))),
            )))
        )))
        self.assertEqual(included, [])

    def test_render_complex_relationship(self):
        """
        Allow specifying a relationship object that specifies additional data for the relationship.
        Relationship links will most likely depend on some part of original object's data
        (like the pk)
        """
        class ArtistRelationship(RelationshipObject):
            links = (
                ('self', UrlLink(view_name='album-relationship-artist', url_kwargs={'pk': 'id'})),
                ('related', UrlLink(view_name='album-related-artist', url_kwargs={'pk': 'id'})),
            )
            meta = {'foo': 'bar'}

        class AlbumObject(ResourceObject):
            type = 'album'
            relationships = (
                ('album_artist', ArtistRelationship()),
            )
            transformer = CamelCaseTransform

        obj = AlbumObject()

        primary, included = obj.render({'id': '123', 'album_artist': None}, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'album'),
            ('relationships', OrderedDict((
                ('albumArtist', OrderedDict((
                    ('data', None),
                    ('links', OrderedDict((
                        ('self', 'http://testserver/api/album/123/relationship_artist/'),
                        ('related', 'http://testserver/api/album/123/related_artist/')
                    ))),
                    ('meta', {'foo': 'bar'})
                ))),
            )))
        )))
        self.assertEqual(included, [])

    def test_render_included(self):
        """
        You can render included resources
        """
        class ArtistObject(ResourceObject):
            type = 'artist'
            attributes = ('first_name', 'last_name')

        class AlbumObject(ResourceObject):
            type = 'album'
            relationships = ('artist',)

        # This a faked ResourceIdObject that allows you the schema to not know about
        # the serializer directly.
        class ArtistLink(ResourceIdObject):
            def get_schema(self):
                return ArtistObject()

            def get_data(self):
                return {
                    'id': self.id,
                    'first_name': 'John',
                    'last_name': 'Coltrane'
                }

        primary, included = AlbumObject().render({
            'id': '123',
            'artist': ArtistLink(id=5, type='artist')
        }, self.request, parse_include('artist'))
        self.assertEqual(included, [
            OrderedDict((
                ('id', '5'),
                ('type', 'artist'),
                ('attributes', OrderedDict((
                    ('first_name', 'John'),
                    ('last_name', 'Coltrane')
                )))
            ))
        ])

    def test_render_included_path(self):
        """
        You can render included paths.
        """
        class ArtistObject(ResourceObject):
            type = 'artist'
            attributes = ('first_name', 'last_name')
            relationships = ('albums',)

        class AlbumObject(ResourceObject):
            type = 'album'
            attributes = ('name',)
            relationships = ('tracks',)

        class TrackObject(ResourceObject):
            type = 'track'
            attributes = ('name',)

        class TrackLink(ResourceIdObject):
            type = 'track'

            def get_schema(self):
                return TrackObject()

            def get_data(self):
                return {'id': self.id, 'name': self.name}

        # This a faked ResourceIdObject that allows you the schema to not know about
        # the serializer directly.
        class AlbumLink(ResourceIdObject):
            type = 'album'

            def get_schema(self):
                return AlbumObject()

            def get_data(self):
                return {
                    'id': self.id,
                    'name': self.name,
                    'tracks': [
                        TrackLink(id=1, name='Acknowledgement'),
                        TrackLink(id=2, name='Resolution')
                    ]
                }

        primary, included = ArtistObject().render({
            'id': '123',
            'first_name': 'John',
            'last_name': 'Coltrane',
            'albums': [AlbumLink(id=5, name='A Love Supreme')]
        }, self.request, parse_include('albums.tracks'))
        self.assertEqual(included, [
            OrderedDict((
                ('id', '5'),
                ('type', 'album'),
                ('attributes', OrderedDict((
                    ('name', 'A Love Supreme'),
                ))),
                ('relationships', OrderedDict((
                    ('tracks', OrderedDict((
                        ('data', [
                            OrderedDict((('id', '1'), ('type', 'track'))),
                            OrderedDict((('id', '2'), ('type', 'track')))
                        ]),
                    ))),
                )))
            )),
            OrderedDict((
                ('id', '1'),
                ('type', 'track'),
                ('attributes', OrderedDict((
                    ('name', 'Acknowledgement'),
                )))
            )),
            OrderedDict((
                ('id', '2'),
                ('type', 'track'),
                ('attributes', OrderedDict((
                    ('name', 'Resolution'),
                )))
            )),
        ])

    def test_render_invalid_include(self):
        """
        An invalid include path throws an exception.
        """
        class ArtistObject(ResourceObject):
            type = 'artist'
            attributes = ('first_name', 'last_name')
            relationships = ('albums',)

        with self.assertRaises(IncludeInvalid):
            ArtistObject().render({
                'id': '123',
                'first_name': 'John',
                'last_name': 'Coltrane',
                'albums': []
            }, self.request, parse_include('invalid'))

    def test_transform(self):
        """
        You can specify and transform that adjusts the names
        """
        obj = ResourceObject(type='users', attributes=('first_name', 'last_name',),
                             transformer=CamelCaseTransform)
        primary, included = obj.render({
            'id': '123',
            'first_name': 'John',
            'last_name': 'Coltrane'
        }, self.request, {})
        self.assertEqual(primary, OrderedDict((
            ('id', '123'),
            ('type', 'users'),
            ('attributes', OrderedDict((
                ('firstName', 'John'),
                ('lastName', 'Coltrane')
            )))
        )))
        self.assertEqual(included, [])

    def test_parse(self):
        """
        Tests parsing attributes with transforms.
        """
        obj = ResourceObject(type='users', attributes=('first_name', 'last_name',),
                             transformer=CamelCaseTransform)
        result = obj.parse({
            'id': '123',
            'type': 'users',
            'attributes': {
                'firstName': 'John',
                'lastName': 'Coltrane'
            }
        }, self.request)
        self.assertEqual(result, {
            'id': '123',
            'first_name': 'John',
            'last_name': 'Coltrane'
        })

    def test_parse_partial(self):
        """
        Attributes not passed in don't get included in the result data.
        """
        obj = ResourceObject(type='users', attributes=('first_name', 'last_name',),
                             transformer=CamelCaseTransform)
        result = obj.parse({
            'type': 'users',
            'attributes': {
                'firstName': 'John'
            }
        }, self.request)
        self.assertEqual(result, {
            'first_name': 'John'
        })

    def test_parse_type_conflict(self):
        """
        The parser throws a type conflict exception on type conflicts.
        """
        obj = ResourceObject(type='users')
        with self.assertRaises(TypeConflict):
            obj.parse({
                'id': '123',
                'type': 'something'
            }, self.request)
        with self.assertRaises(TypeConflict):
            obj.parse({}, self.request)
