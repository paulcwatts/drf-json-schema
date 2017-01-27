

class NullTransform(object):
    def transform(self, name):
        return name


def _upper(name):
    return name[0].upper() + name[1:] if name else name


class CamelCaseTransform(object):
    def transform(self, name):
        split = name.split('_')
        return split[0] + ''.join([_upper(c) for c in split[1:]])


class CamelCaseToUnderscoreTransform(object):
    def transform(self, name):
        words = []
        last = 0

        for i, c in enumerate(name):
            if c[0].isupper():
                # Start of a new word
                words.append(name[last].lower() + name[last + 1:i])
                last = i
        # Add the last word
        words.append(name[last].lower() + name[last + 1:])

        return '_'.join(words)
