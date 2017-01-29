from django.test import SimpleTestCase

from rest_framework_json_schema.utils import parse_include


class ParseIncludeTestCase(SimpleTestCase):
    def test_empty(self):
        result = parse_include('')
        self.assertEqual(result, {})

    def test_single(self):
        result = parse_include('a')
        self.assertEqual(result, {'a': {}})

    def test_complicated(self):
        result = parse_include('a,a.b,a.c.d,e.f,g')
        self.assertEqual(result, {
            'a': {
                'b': {},
                'c': {
                    'd': {}
                }
            },
            'e': {
                'f': {}
            },
            'g': {}
        })
