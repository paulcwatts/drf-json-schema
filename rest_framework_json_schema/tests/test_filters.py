from rest_framework.test import APISimpleTestCase

from rest_framework_json_schema.filters import get_query_filters
from rest_framework_json_schema.transforms import CamelCaseToUnderscoreTransform


class JSONAPIFilterTestCase(APISimpleTestCase):
    def test_filter_no_transform(self):
        result = get_query_filters({
            'filter[name]': 'John',
            'filter[lastName]': 'Coltrane',
            'limit': 50
        })
        self.assertEqual(result, {
            'name': 'John',
            'lastName': 'Coltrane'
        })

    def test_filter_transform(self):
        result = get_query_filters({
            'filter[name]': 'John',
            'filter[lastName]': 'Coltrane',
            'limit': 50
        }, CamelCaseToUnderscoreTransform())
        self.assertEqual(result, {
            'name': 'John',
            'last_name': 'Coltrane'
        })
