from django.db import models
from rest_framework import serializers

from rest_framework_json_schema.auto import from_serializer, auto_schema
from rest_framework_json_schema.schema import ResourceObject
from rest_framework_json_schema.transforms import CamelCaseTransform


class MyModel(models.Model):
    my_int = models.IntegerField()
    my_str = models.CharField()

    class Meta:
        app_label = "auto_test"


class RelModel(models.Model):
    my_rel = models.ForeignKey(MyModel, on_delete=models.CASCADE)
    int_rel = models.IntegerField()

    class Meta:
        app_label = "auto_test"


class NonIdModel(models.Model):
    my_id = models.AutoField(primary_key=True)
    my_int = models.IntegerField()

    class Meta:
        app_label = "auto_test"


def test_from_serializer() -> None:
    """Basic creation of a schema."""

    class MySerializer(serializers.Serializer):
        id = serializers.IntegerField()
        int_attr = serializers.IntegerField()
        my_attr = serializers.CharField()

    result = from_serializer(MySerializer(), "mytype")
    assert isinstance(result, type(ResourceObject))
    assert result.type == "mytype"
    assert result.id == "id"
    assert result.attributes == ["int_attr", "my_attr"]
    assert result.relationships == []


def test_from_model_serializer() -> None:
    """Given a model serializer, it respects the order of Meta.fields."""

    class MySerializer(serializers.ModelSerializer):
        class Meta:
            model = MyModel
            fields = ["id", "my_str", "my_int"]

    result = from_serializer(MySerializer(), "mymodel")
    assert isinstance(result, type(ResourceObject))
    assert result.type == "mymodel"
    assert result.id == "id"
    assert result.attributes == ["my_str", "my_int"]
    assert result.relationships == []


def test_model_relations() -> None:
    """Given a model serializer, it adds relationships."""

    class MySerializer(serializers.ModelSerializer):
        class Meta:
            model = RelModel
            fields = ["id", "int_rel", "my_rel"]

    result = from_serializer(MySerializer(), "myrel")
    assert isinstance(result, type(ResourceObject))
    assert result.type == "myrel"
    assert result.id == "id"
    assert result.attributes == ["int_rel"]
    assert result.relationships == ["my_rel"]


def test_non_id_primary() -> None:
    """Test where a model has a pk not named "id"."""

    class NonIdSerializer(serializers.ModelSerializer):
        class Meta:
            model = NonIdModel
            fields = ["my_id", "my_int"]

    result = from_serializer(NonIdSerializer(), "nonid")
    assert isinstance(result, type(ResourceObject))
    assert result.type == "nonid"
    assert result.id == "my_id"
    assert result.attributes == ["my_int"]
    assert result.relationships == []


def test_extra_params() -> None:
    """Extra parameters are passed along to the schema."""

    class MySerializer(serializers.Serializer):
        id = serializers.IntegerField()
        my_attr = serializers.CharField()

    result = from_serializer(MySerializer(), "mytype", transformer=CamelCaseTransform)
    assert isinstance(result, type(ResourceObject))
    assert result.transformer == CamelCaseTransform


def test_descriptor() -> None:
    """You can use the auto_schema descriptor."""

    class MySerializer(serializers.Serializer):
        id = serializers.IntegerField()
        my_attr = serializers.CharField()

        schema = auto_schema("mytype", transformer=CamelCaseTransform)

    serializer = MySerializer()
    result = serializer.schema()
    assert isinstance(result, ResourceObject)
    assert result.type == "mytype"
    assert result.id == "id"
    assert result.attributes == ["my_attr"]
    assert result.relationships == []
    assert result.transformer == CamelCaseTransform
