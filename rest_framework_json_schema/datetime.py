from datetime import datetime


def api_format(value: datetime) -> str:
    """Copied from the DRF DateTimeField -- formats ISO like DRF does."""
    result = value.isoformat()
    if result.endswith("+00:00"):
        result = result[:-6] + "Z"
    return result
