"""Transformer classes used by the schema."""

from abc import ABC, abstractmethod
from typing import List


class Transform(ABC):
    """Provide the base interface for transforms."""

    @abstractmethod
    def transform(self, name: str) -> str:
        """Return the transformed name."""
        ...


class NullTransform(Transform):
    """A transform that doesn't do anything."""

    def transform(self, name: str) -> str:
        """Do nothing."""
        return name


def _upper(name: str) -> str:
    return name[0].upper() + name[1:] if name else name


class CamelCaseTransform(Transform):
    """Transform snake_underscore_case to camelCase."""

    def transform(self, name: str) -> str:
        """Transform snake_underscore_case to camelCase."""
        split = name.split("_")
        return split[0] + "".join([_upper(c) for c in split[1:]])


class CamelCaseToUnderscoreTransform(Transform):
    """Transform camelCase to snake_underscore_case."""

    def transform(self, name: str) -> str:
        """Transform camelCase to snake_underscore_case."""
        words: List[str] = []
        last = 0

        for i, c in enumerate(name):
            if c[0].isupper():
                # Start of a new word
                words.append(name[last].lower() + name[last + 1 : i])
                last = i
        # Add the last word
        words.append(name[last].lower() + name[last + 1 :])

        return "_".join(words)
