import pytest
from rest_framework.test import APIRequestFactory

from tests.support.serializers import reset_data


@pytest.fixture
def factory() -> APIRequestFactory:
    """Provide an API Request Factory."""
    return APIRequestFactory()


@pytest.fixture(autouse=True)
def auto_reset_data() -> None:
    """Automatically reset test data before each test."""
    reset_data()
