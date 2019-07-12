"""Setup script for drf-json-schema."""

from setuptools import setup

import rest_framework_json_schema

setup(
    name="drf_json_schema",
    version=rest_framework_json_schema.__version__,
    packages=["rest_framework_json_schema", "rest_framework_json_schema.migrations"],
    url="https://github.com/paulcwatts/drf-json-schema",
    license="MIT",
    author="Paul Watts",
    author_email="paulcwatts@gmail.com",
    description="Extensible JSON API schema for Django Rest Framework",
    keywords=["django", "jsonapi", ""],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
