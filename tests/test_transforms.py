from rest_framework_json_schema.transforms import (
    CamelCaseTransform,
    CamelCaseToUnderscoreTransform,
)


def test_camel_case_transform() -> None:
    tx = CamelCaseTransform()

    assert tx.transform("one") == "one"
    assert tx.transform("one_two_three") == "oneTwoThree"


def test_camel_case_to_underscore_transform() -> None:
    tx = CamelCaseToUnderscoreTransform()

    assert tx.transform("one") == "one"
    assert tx.transform("oneTwoThree") == "one_two_three"
