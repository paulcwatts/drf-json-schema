"""Datetime utilities."""


from datetime import datetime


def api_format(value: datetime) -> str:
    """
    Format a datetime as ISO like DRF does.

    Copied from the DRF DateTimeField.
    """
    result = value.isoformat()
    if result.endswith("+00:00"):
        result = result[:-6] + "Z"
    return result
