=========================================
JSON API Schema for Django REST Framework
=========================================

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black
.. image:: http://www.mypy-lang.org/static/mypy_badge.svg
    :target: http://mypy-lang.org/
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://github.com/paulcwatts/drf-json-schema/blob/master/LICENSE.txt

An implementation of the `JSON API <http://jsonapi.org/>`_ specification for Django REST Framework,
specifically designed to be extensible and work with code that doesn't use ``ModelSerializer``.

Tested with:

* Python 3.6+
* Django 2.2, 3.11+ 
* Django REST Framework: 3.9+

Development
===========

To begin contributing to the code:

* ``git clone https://github.com/paulcwatts/drf-json-schema.git``
* ``pipenv install --dev``
* ``pipenv run pip install django djangorestframework``
* ``pipenv run pre-commit install``

To run the tests using nox:

* ``pipx install nox``
* ``nox``
