from rest_framework_json_schema.filters import get_query_filters
from rest_framework_json_schema.transforms import CamelCaseToUnderscoreTransform


def test_filter_no_transform() -> None:
    """The transform works with no filter."""
    result = get_query_filters({
        'filter[name]': 'John',
        'filter[lastName]': 'Coltrane',
        'limit': 50
    })
    assert result == {
        'name': 'John',
        'lastName': 'Coltrane'
    }


def test_filter_transform() -> None:
    """Given a transform, the filter applies correctly."""
    result = get_query_filters({
        'filter[name]': 'John',
        'filter[lastName]': 'Coltrane',
        'limit': 50
    }, CamelCaseToUnderscoreTransform())
    assert result == {
        'name': 'John',
        'last_name': 'Coltrane'
    }
