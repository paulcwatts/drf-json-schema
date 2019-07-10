=========================================
JSON API Schema for Django REST Framework
=========================================

.. image:: https://travis-ci.org/paulcwatts/drf-json-schema.svg?branch=master
    :target: https://travis-ci.org/paulcwatts/drf-json-schema
.. image:: https://codecov.io/gh/paulcwatts/drf-json-schema/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/paulcwatts/drf-json-schema

An implementation of the `JSON API <http://jsonapi.org/>`_ specification for Django REST Framework,
specifically designed to be extensible and work with code that doesn't use ``ModelSerializer``.

Tested with:

* Python 3.6+
* Django 2.0+ 
* Django REST Framework: 3.8+

Development
===========

* ``pipx install nox``
* ``nox``
