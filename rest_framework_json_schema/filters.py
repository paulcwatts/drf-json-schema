"""Utilities and helpers for filtering."""

import re
from typing import Any, Dict, Optional

from .transforms import NullTransform, Transform

FILTER = re.compile(r"^filter\[(\w+)\]$")


def get_query_filters(
    params: Dict[str, Any], transformer: Optional[Transform] = None
) -> Dict[str, Any]:
    """
    Parse JSON API filter query parameters and apply an optional transformation.

    https://jsonapi.org/format/#fetching-filtering
    """

    result = {}
    transformer = transformer or NullTransform()

    for key, value in params.items():
        m = FILTER.match(key)
        if m:
            result[transformer.transform(m.group(1))] = value

    return result
