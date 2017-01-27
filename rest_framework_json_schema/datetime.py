

def api_format(value):
    """
    Copied from the DRF DateTimeField -- formats ISO like DRF does.
    """
    value = value.isoformat()
    if value.endswith('+00:00'):
        value = value[:-6] + 'Z'
    return value
