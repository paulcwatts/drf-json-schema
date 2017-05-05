import json

from django.core.urlresolvers import reverse
from django.test import override_settings
from rest_framework.test import APISimpleTestCase, APIRequestFactory

from rest_framework_json_schema.test_support.serializers import reset_data
from rest_framework_json_schema.test_support.views import ArtistViewSet, AlbumViewSet, TrackViewSet


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPIAttributesRendererTestCase(APISimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view_list = ArtistViewSet.as_view({'get': 'list'})
        self.view_detail = ArtistViewSet.as_view({'get': 'retrieve'})
        reset_data()

    def test_detail_attributes(self):
        """
        You can render primary data object attributes
        """
        request = self.factory.get(reverse('artist-detail', kwargs={'pk': 1}))
        response = self.view_detail(request, pk=1)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '1',
                'type': 'artist',
                'attributes': {
                    'firstName': 'John',
                    'lastName': 'Coltrane'
                }
            }
        })

    def test_list_attributes(self):
        """
        You can render primary data list attributes
        """
        request = self.factory.get(reverse('artist-list'))
        response = self.view_list(request)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')

        data = json.loads(response.content.decode())['data']
        self.assertEqual(data[:3], [
            {
                'id': '0',
                'type': 'artist',
                'attributes': {'firstName': 'Miles', 'lastName': 'Davis'}
            },
            {
                'id': '1',
                'type': 'artist',
                'attributes': {'firstName': 'John', 'lastName': 'Coltrane'}
            },
            {
                'id': '2',
                'type': 'artist',
                'attributes': {'firstName': 'Charles', 'lastName': 'Mingus'}
            }
        ])

    def test_empty_list(self):
        """
        The 'data' field appears in the top-level object even if data is empty.
        """
        request = self.factory.get(reverse('artist-list'), {'filter[firstName]': 'Foo'})
        response = self.view_list(request)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': []
        })

    def test_exception(self):
        """
        The renderer handles thrown exceptions.
        """
        request = self.factory.get(reverse('artist-detail', kwargs={'pk': 8}))
        response = self.view_detail(request, pk=8)
        response.render()
        self.assertJSONEqual(response.content.decode(), {
            'errors': [
                {
                    'detail': 'Not found.'
                }
            ]
        })

    def test_options(self):
        request = self.factory.options(reverse('artist-list'))
        response = self.view_list(request)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'meta': {
                'data': {
                    'description': 'A simple ViewSet for listing or retrieving artists.',
                    'name': 'Artist',
                    'parses': ['application/vnd.api+json'],
                    'renders': ['application/vnd.api+json']
                }
            }
        })

    def test_fields(self):
        url = reverse('artist-detail', kwargs={'pk': 1})
        request = self.factory.get(url, {'fields[artist]': 'firstName'})
        response = self.view_detail(request, pk=1)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '1',
                'type': 'artist',
                'attributes': {
                    'firstName': 'John',
                }
            }
        })


@override_settings(ROOT_URLCONF='rest_framework_json_schema.test_support.urls')
class JSONAPIRelationshipsRendererTestCase(APISimpleTestCase):
    maxDiff = None

    def setUp(self):
        self.factory = APIRequestFactory()
        # self.view_list = AlbumViewSet.as_view({'get': 'list'})
        self.view_detail = AlbumViewSet.as_view({'get': 'retrieve'})
        reset_data()

    def test_empty(self):
        """
        You can render empty relationships
        """
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 3}))
        response = self.view_detail(request, pk=3)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '3',
                'type': 'album',
                'attributes': {
                    'albumName': 'Unknown Artist'
                },
                'relationships': {
                    'artist': {
                        'data': None
                    },
                    'tracks': {
                        'data': []
                    }
                }
            }
        })

    def test_to_one_non_empty(self):
        """
        You can render a non-empty to-one relationship.
        """
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 0}))
        response = self.view_detail(request, pk=0)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '0',
                'type': 'album',
                'attributes': {
                    'albumName': 'A Love Supreme'
                },
                'relationships': {
                    'artist': {
                        'data': {'id': '1', 'type': 'artist'}
                    },
                    'tracks': {
                        'data': []
                    }
                }
            }
        })

    def test_to_many_non_empty(self):
        """
        You can render a non-empty to-many relationship.
        """
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 1}))
        response = self.view_detail(request, pk=1)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '1',
                'type': 'album',
                'attributes': {
                    'albumName': 'Birth of the Cool'
                },
                'relationships': {
                    'artist': {
                        'data': {'id': '0', 'type': 'artist'}
                    },
                    'tracks': {
                        'data': [
                            {'id': '0', 'type': 'track'},
                            {'id': '1', 'type': 'track'},
                            {'id': '2', 'type': 'track'},
                            {'id': '3', 'type': 'track'},
                        ]
                    }
                }
            }
        })

    def test_include_to_one(self):
        """
        You can include a to-one relationship as a compound document
        """
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 0}),
                                   {'include': 'artist'})
        response = self.view_detail(request, pk=0)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '0',
                'type': 'album',
                'attributes': {
                    'albumName': 'A Love Supreme'
                },
                'relationships': {
                    'artist': {
                        'data': {'id': '1', 'type': 'artist'}
                    },
                    'tracks': {
                        'data': []
                    }
                }
            },
            'included': [
                {
                    'id': '1',
                    'type': 'artist',
                    'attributes': {
                        'firstName': 'John',
                        'lastName': 'Coltrane'
                    }
                }
            ]
        })

    def test_include_to_many_and_paths(self):
        """
        You can include a to-many relationship as a compound document
        """
        track_detail = TrackViewSet.as_view({'get': 'retrieve'})
        request = self.factory.get(reverse('track-detail', kwargs={'pk': 0}),
                                   {'include': 'album,album.artist,album.tracks'})
        response = track_detail(request, pk=0)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '0',
                'type': 'track',
                'attributes': {
                    'name': 'Jeru',
                    'trackNum': 1
                },
                'relationships': {
                    'album': {
                        'data': {'id': '1', 'type': 'album'}
                    }
                }
            },
            'included': [
                {
                    'id': '1',
                    'type': 'album',
                    'attributes': {
                        'albumName': 'Birth of the Cool'
                    },
                    'relationships': {
                        'artist': {
                            'data': {'id': '0', 'type': 'artist'}
                        },
                        'tracks': {
                            'data': [
                                {'id': '0', 'type': 'track'},
                                {'id': '1', 'type': 'track'},
                                {'id': '2', 'type': 'track'},
                                {'id': '3', 'type': 'track'},
                            ]
                        }
                    }
                },
                {
                    'id': '0',
                    'type': 'artist',
                    'attributes': {
                        'firstName': 'Miles',
                        'lastName': 'Davis'
                    }
                },
                {
                    'id': '0',
                    'type': 'track',
                    'attributes': {
                        'name': 'Jeru',
                        'trackNum': 1
                    },
                    'relationships': {
                        'album': {
                            'data': {'id': '1', 'type': 'album'}
                        }
                    }
                },
                {
                    'id': '1',
                    'type': 'track',
                    'attributes': {
                        'name': 'Moon Dreams',
                        'trackNum': 2
                    },
                    'relationships': {
                        'album': {
                            'data': {'id': '1', 'type': 'album'}
                        }
                    }
                },
                {
                    'id': '2',
                    'type': 'track',
                    'attributes': {
                        'name': 'Venus de Milo',
                        'trackNum': 3
                    },
                    'relationships': {
                        'album': {
                            'data': {'id': '1', 'type': 'album'}
                        }
                    }
                },
                {
                    'id': '3',
                    'type': 'track',
                    'attributes': {
                        'name': 'Deception',
                        'trackNum': 4
                    },
                    'relationships': {
                        'album': {
                            'data': {'id': '1', 'type': 'album'}
                        }
                    }
                }
            ]
        })

    def test_fields(self):
        request = self.factory.get(reverse('album-detail', kwargs={'pk': 0}),
                                   {'fields[album]': 'artist',
                                    'fields[artist]': 'firstName',
                                    'include': 'artist'})
        response = self.view_detail(request, pk=0)
        response.render()
        self.assertEqual(response['Content-Type'], 'application/vnd.api+json')
        self.assertJSONEqual(response.content.decode(), {
            'data': {
                'id': '0',
                'type': 'album',
                'relationships': {
                    'artist': {
                        'data': {'id': '1', 'type': 'artist'}
                    }
                }
            },
            'included': [
                {
                    'id': '1',
                    'type': 'artist',
                    'attributes': {
                        'firstName': 'John'
                    }
                }
            ]
        })
