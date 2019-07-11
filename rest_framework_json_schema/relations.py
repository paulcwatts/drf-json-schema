from typing import Any, Dict, Type

from django.utils.module_loading import import_string
from rest_framework import serializers

from .schema import ResourceIdObject, ResourceObject


class ResourceIdField(ResourceIdObject):
    def __init__(
        self, serializer: Type[serializers.Serializer], instance: Any, **kwargs: Any
    ) -> None:
        self.serializer = serializer
        self.instance = instance
        super().__init__(**kwargs)

    def get_schema(self) -> ResourceObject:
        return self.serializer.schema()

    def get_data(self) -> Dict[str, Any]:
        return self.serializer(self.instance).data


class JSONAPIRelationshipField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs: Any) -> None:
        self.type = kwargs.pop("type", None)
        self.serializer = kwargs.pop("serializer", None)
        self._serializer = None
        if not isinstance(self.serializer, str):
            self._serializer = self.serializer

        assert (
            self.type or self.serializer
        ), "JSONAPIRelationshipField must either specify a `type` or `serializer."
        super().__init__(**kwargs)

    def use_pk_only_optimization(self) -> bool:
        # We can use the pk-only optimization if the parent's object
        # is not included in the 'include' query parameter in some form.
        request = self.context.get("request", None)
        if not request:
            # To be on the safe side -- this usually happens when we
            # are in a multi-level include scenario.
            return False

        include = request.query_params.get("include")
        # Because we can't tell what "level" of inclusion we're at,
        # the only safe thing we can do is to turn off the optimization
        # if the include parameter exists.
        return not include

    def get_serializer(self) -> Type[serializers.Serializer]:
        if not self._serializer:
            # If the serializer value is a string, try to import it.
            if isinstance(self.serializer, str):
                self._serializer = import_string(self.serializer)

        return self._serializer

    def get_type(self) -> str:
        if self.type:
            return self.type
        return self.get_serializer().schema().type

    def to_representation(self, value: Any) -> Any:
        id = super().to_representation(value)
        serializer = self.get_serializer()

        if serializer:
            # Wrap this in our special ResourceIdField that can fetch and serialize
            # this included relation.
            return ResourceIdField(serializer, value, id=id, type=self.get_type())
        else:
            # If we don't have a serializer, we cannot include this relationship.
            return ResourceIdObject(id=id, type=self.get_type())
