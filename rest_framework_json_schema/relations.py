from rest_framework import serializers

from .schema import ResourceIdObject


class JSONAPIRelationshipField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.type = kwargs.pop('type', None)
        self.serializer = kwargs.pop('serializer', None)

        assert self.type or self.serializer, (
            'JSONAPIRelationshipField must either specify a `type` or `serializer.'
        )

        if not self.type:
            # Get the type from the provided serializer
            self.type = self.serializer.schema().type

        super(JSONAPIRelationshipField, self).__init__(**kwargs)

    def to_representation(self, value):
        # Call the super class to get the primary key
        # original = value
        id = super(JSONAPIRelationshipField, self).to_representation(value)
        return ResourceIdObject(id=id, type=self.type)
