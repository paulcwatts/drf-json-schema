from django.test import SimpleTestCase

from rest_framework_json_schema.transforms import CamelCaseTransform, CamelCaseToUnderscoreTransform


class CamelCaseTransformTestCase(SimpleTestCase):
    def test_transform(self):
        tx = CamelCaseTransform()

        self.assertEqual(tx.transform('one'), 'one')
        self.assertEqual(tx.transform('one_two_three'), 'oneTwoThree')


class CamelCaseToUnderscoreTransformTestCase(SimpleTestCase):
    def test_transform(self):
        tx = CamelCaseToUnderscoreTransform()

        self.assertEqual(tx.transform('one'), 'one')
        self.assertEqual(tx.transform('oneTwoThree'), 'one_two_three')
