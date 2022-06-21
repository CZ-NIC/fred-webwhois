ChangeLog
=========

Unreleased
----------

2.1.0 (2022-06-21)
-------------------

* Drop support for Django 2.2.
* Update supported IDL versions.
* Add ``PublicResponseView`` and ``PublicResponsePdfView`` and use them by default (#2).
* Separate ``PublicResponseMixin`` (#2).
* Update ``.dockerignore``.

2.0.0 (2022-05-30)
-------------------

* Drop support for Python 3.6 and 3.7.
* Add support for Python 3.10.
* Drop support for Django 3.0 and 3.1.
* Add ``managed_zones`` context processor.
  Context variable ``managed_zone_list`` is now deprecated and replaced by ``managed_zones`` provided
  by the context processor.
* Refactored error handling in whois search.
  Variable ``server_exception`` is now a ``WebwhoisError`` instance with deprecated backwards compatible dictionary API.
* Refactor object loading. Method ``load_registry_object`` is not deprecated.
* Rename logger services.
* Refactor public request logging. Log data are now processed in forms.
* Switch logging to FRED logger from ``pylogger`` to ``grill`` library.
  This change is backwards incompatible: new library and settings are used.
  The structure of logs is left intact.
  ``LoggerMixin`` is deleted.
* Add logger related constants.
* Use ``statementor`` library to generate record statements.
* A setting ``WEBWHOIS_LOGGER`` now supports only ``grill`` compatible logger clients.
* Add new settings ``WEBWHOIS_LOGGER_OPTIONS``, ``WEBWHOIS_REGISTRY_NETLOC``, ``WEBWHOIS_REGISTRY_SSL_CERT``,
  ``WEBWHOIS_SECRETARY_AUTH``, ``WEBWHOIS_SECRETARY_TIMEOUT`` and ``WEBWHOIS_SECRETARY_URL``.
* Drop settings ``WEBWHOIS_LOGGER_CORBA_NETLOC``, ``WEBWHOIS_LOGGER_CORBA_CONTEXT`` and
  ``WEBWHOIS_LOGGER_CORBA_OBJECT``.
* Add a default design.
* Add utilities for deprecation warnings.
* Clean up deprecation warnings.
* Update static checks, CI & project setup.

1.20.2 (2022-02-14)
-------------------

* Make requirements for cdnskey scan results optional.

1.20.1 (2021-08-31)
-------------------

* Forbid '/' in whois form input.

1.20.0 (2021-07-07)
-------------------

* Drop support for Python 3.5.
* Drop support for Django < 2.2.
* Add support for Python 3.9.
* Add support for Django 3.1 and 3.2.
* Update ``webwhois.urls`` to Django 2+.
  Slight changes occured, e.g. ``/`` is no longer matched as part of a ``handle``.
  These changes shouldn't affect the usage.
* Add cdnskey scan results.
* Refactor DNS key algorithms & flags to enums.
* Fix wording.
* Fix settings description in readme.
* Update style check & CI setup.

1.19.0 (2021-05-11)
-------------------

* Add support for Python 3.9.
* Add support for Django 3.1.
* Add production ready ``Dockerfile``.

1.18.1 (2020-11-24)
-------------------

* Fix tag mistake.
* Rename `CHANGELOG.rst`.
* Update CI setup.

1.18 (2020-10-01)
-----------------

* Add support for Python 3.8.
* Add support for Django 3.0.
* Add ``WEBWHOIS_LOGGER_CORBA_OBJECT`` setting.
* Drop setting ``WEBWHOIS_DNSSEC_URL``.
* Clean deprecated parts of registrar list mixin.
  * Deprecate ``is_retail`` context variable in registrar list mixin.
* Fix page titles.
* Style fixes on public request pages.
* Update style checks, add bumpversion.
* Reformat Chnagelog.

1.17 (2020-03-03)
-----------------

* Refactor public requests
* Drop support for python 2.7
* Drop deprecated ``PublicRequestBaseForm.CONFIRMATION_METHOD``
* Drop deprecated usage of pylogger
* Update implementation of ``WEBWHOIS_LOGGER`` setting
* Update development tools settings, add mypy

1.16.1 (2019-11-20)
-------------------

* Update spec file for F31 and Centos/RHEL 8

1.16 (2019-10-23)
-----------------

* Support Django 2.X
* Use PEP508 dependencies

1.15 (2019-03-21)
-----------------

* Remove ``handle_is_domain`` from ``DomainDetailMixin``
* Remove ``webwhois.views.pages`` module
* Refactor view for list of registrars
* Clean up CSS styles in request forms

1.14.1 (2019-02-06)
-------------------

* Temporarily return status codes to HTML data attributes

1.14 (2018-07-27)
-----------------

* Add Python 3 and Django 2.0 support
* Improve behaviour of confirmation methods in public requests
* Add public response object to context of public response views
* Add government confirmation method for public requests
* New behavior in case no object was found for a handle
* Fix wording of error message in personal info public request
* Fix unmanaged zone behaviour
* Remove status codes from HTML data attributes
* Remove public response backports
* Remove links for search engines and domain registration from settings and templates
* Remove ``webwhois_base_template`` attribute from views. Use ``base_template`` instead
* Remove CZ.NIC specific webwhois templates
* Remove obsolete ``default_app_config``
* Fix Fedora builds

1.13 (2018-04-18)
-----------------

* Add personal info public request
* Refactor public request responses
* Drop support for old IDL structures
* Remove CZ.NIC specific code - public request descriptions, dobradomena and registrar links
* Clean up code - pyfco deprecation warnings
* Support omniidl up to 4.2.2
* Use tox for testing

1.12.2 (2018-04-24)
-------------------

* Fix detail of ENUM domains

1.12.1 (2018-04-17)
-------------------

* Fix response for domains in delete candidate status

1.12 (2018-03-08)
-----------------

* Prepare for Python 3 - clean up code and use ``unicode_literals``
* Support new ISO date time and buffer structures from IDLs
* Handle new ``OBJECT_DELETE_CANDIDATE`` exception
* Use ``Babel`` for package distribution
* Remove mojeid contact view
* Move whois form to webwhois index
* Fix up tests
* Fix RPM builds

1.11 (2018-02-12)
-----------------

* Add changelog
* Use ``setuptools`` for packaging
* Drop example ``webwhois_site``
* Define constants for statuses
* Handle delete candidate objects
