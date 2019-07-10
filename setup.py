from setuptools import setup, find_packages

import rest_framework_json_schema

setup(
    name="drf_json_schema",
    version=rest_framework_json_schema.__version__,
    packages=find_packages(),
    url="https://github.com/paulcwatts/drf-json-schema",
    license="MIT",
    author="Paul Watts",
    author_email="paulcwatts@gmail.com",
    description="Extensible JSON API schema for Django Rest Framework",
    keywords=["django", "jsonapi", ""],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django :: 1.9",
        "Framework :: Django :: 1.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
