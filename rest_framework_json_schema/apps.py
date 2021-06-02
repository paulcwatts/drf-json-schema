"""Needed to be a Django app."""

from django.apps import AppConfig


class DrfJsonConfig(AppConfig):
    """
    App config.

    Reference: `Django applications <https://docs.djangoproject.com/en/3.2/ref/applications/>`

    :param name: Full Python path to the application
    :type name: str
    :param verbose_name: Human-readable name for the application
    :type verbose_name: str
    """

    name = "rest_framework_json_schema"
    verbose_name = "JSON API Schema for Django REST Framework"
