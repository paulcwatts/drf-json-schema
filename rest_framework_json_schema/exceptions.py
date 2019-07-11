"""Exceptions defined by JSON API."""


class TypeConflict(Exception):
    """
    The type passed to this resource object is incorrect.

    https://jsonapi.org/format/#crud-creating-responses-409
    """


class IncludeInvalid(Exception):
    """
    The relationship cannot be included.

    https://jsonapi.org/format/#fetching-includes
    """


class NoSchema(Exception):
    """
    Schema not found on the data to render.

    This is a programmer error.
    """
