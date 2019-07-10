from rest_framework_json_schema.utils import parse_include


def test_parse_include_empty() -> None:
    result = parse_include("")
    assert result == {}


def test_parse_include_single() -> None:
    result = parse_include("a")
    assert result == {"a": {}}


def test_parse_include_complicated() -> None:
    result = parse_include("a,a.b,a.c.d,e.f,g")
    assert result == {"a": {"b": {}, "c": {"d": {}}}, "e": {"f": {}}, "g": {}}
