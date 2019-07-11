"""Helper classes for serializers and paginators."""

from typing import Any

from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


class JSONReturnList(ReturnList):
    """Extend a DRF ReturnList to include meta and links."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a return list."""
        self.meta = kwargs.pop("meta", None)
        self.links = kwargs.pop("links", None)
        super().__init__(*args, **kwargs)


class JSONReturnDict(ReturnDict):
    """Extend a DRF ReturnList to include meta and links."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Create a return dict."""
        self.meta = kwargs.pop("meta", None)
        self.links = kwargs.pop("links", None)
        super().__init__(*args, **kwargs)
