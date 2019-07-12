"""Generate schemas from DRF serializers."""

from typing import Any, Dict, Type, TypeVar, Generic, List, Optional

from rest_framework import serializers

from .schema import ResourceObject

T = TypeVar("T", bound=serializers.Serializer)


def from_serializer(
    serializer: serializers.Serializer,
    api_type: str,
    *,
    id_field: str = "",
    **kwargs: Any,
) -> Type[ResourceObject]:
    """
    Generate a schema from a DRF serializer.

    :param serializer: The serializer instance.
    :param api_type: The JSON API resource type.
    :param id_field: The 'id" field of the resource.
        If left empty, it is either "id" for non-model serializers, or
        for model serializers, it is looked up on the model.
    :param kwargs: Extra options (like links and transforms) passed to the schema.
    :return: The new schema class.
    """

    # get_fields() should return them in the order of Meta.fields
    serializer_name = type(serializer).__name__

    attrs: List[str] = []
    rels: List[str] = []

    if not id_field:
        # If this is a model serializer, we can reach in to the model
        # and look for the model's PK.
        if isinstance(serializer, serializers.ModelSerializer):
            model = serializer.Meta.model
            for db_field in model._meta.get_fields():
                if db_field.primary_key:
                    id_field = db_field.attname
                    break

            if not id_field:
                raise ValueError(f"Unable to find primary key from model: {model}")
        else:
            # Otherwise, just assume it's "id"
            id_field = "id"

    for field_name, field in serializer.get_fields().items():
        if field_name != id_field:
            if isinstance(field, serializers.RelatedField):
                rels.append(field_name)
            else:
                attrs.append(field_name)

    values: Dict[str, Any] = {
        "id": id_field,
        "type": api_type,
        "attributes": attrs,
        "relationships": rels,
    }
    values.update(**kwargs)
    return type(f"{serializer_name}_AutoSchema", (ResourceObject,), values)


class AutoSchemaDescriptor(Generic[T]):
    """Descriptor used to implement auto_schema."""

    def __init__(
        self, api_type: str, id_field: str, init_kwargs: Dict[str, Any]
    ) -> None:
        """Create the descriptor."""
        self.api_type = api_type
        self.id_field = id_field
        self.init_kwargs = init_kwargs
        self._cached: Optional[Type[ResourceObject]] = None

    def __get__(self, serializer: T, objtype: Type[T]) -> Type[ResourceObject]:
        """Generate the serializer."""
        if not self._cached:
            self._cached = from_serializer(
                serializer, self.api_type, id_field=self.id_field, **self.init_kwargs
            )
        return self._cached


def auto_schema(
    api_type: str, *, id_field: str = "", **kwargs: Any
) -> AutoSchemaDescriptor:
    """
    Generate a schema from this serializer.

    Usage:
        ``
        from rest_framework_json_schema.auto import auto_schema

        class ArtistSerializer:
            schema = auto_schema("artists")
        ``

    You can create a wrapper function to provide defaults:

        ``
        from rest_framework_json_schema.auto import auto_schema
        from rest_framework_json_schema.transforms import CamelCaseTransform

        def my_auto_schema(*args, **kwargs):
            return auto_schema(*args, **kwargs, transform=CamelCaseTransform)
        ``

    :param api_type: The JSON API resource type.
    :param id_field: The 'id" field of the resource.
        If left empty, it is either "id" for non-model serializers, or
        for model serializers, it is looked up on the model.
    :param kwargs: Extra options (like links and transforms) passed to the schema.
    :return: The new schema class.
    """
    return AutoSchemaDescriptor(api_type, id_field, kwargs)
