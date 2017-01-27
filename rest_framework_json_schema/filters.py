import re

from .transforms import NullTransform


FILTER = re.compile(r'^filter\[(\w+)\]$')


def get_query_filters(params, transformer=None):
    result = {}
    transformer = transformer or NullTransform()

    for key, value in params.items():
        m = FILTER.match(key)
        if m:
            result[transformer.transform(m.group(1))] = value

    return result
