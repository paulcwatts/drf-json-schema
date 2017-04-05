

class TypeConflict(Exception):
    """
    The type passed to this resource object is incorrect.
    """


class IncludeInvalid(Exception):
    """
    This relationship cannot be included.
    """


class NoSchema(Exception):
    """
    Schema not found on the data to render.
    """
