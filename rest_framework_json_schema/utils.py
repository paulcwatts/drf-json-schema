def parse_include(include):
    """
    Parses an include parameter into its constituent paths.
    It returns a tree of include paths, for instance:

    a,a.b,a.c.d,e.f,g

    Returns:
    {
        'a': {
            'b': {},
            'c', {
                'd': {}
            }
        },
        'e': {
            'f': {}
        },
        'g': {}
    }
    """
    result = {}
    split = include.split(",")
    for path in split:
        if path:
            components = path.split(".")
            level = result
            for c in components:
                if c not in level:
                    level[c] = {}
                level = level[c]
    return result
