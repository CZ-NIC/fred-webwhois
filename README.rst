========
Webwhois
========

The **Webwhois** is a Django application with the Whois service for the FRED registry system.
The application searches domain names, contacts, nameserver sets and key sets.


Dependencies
============

- python >=3.7
- Other dependencies are listed in `<setup.cfg>`_.


A part of the FRED system
=========================

The ``webwhois`` is a part of the FRED_ system for managing domain names.
The easiest way to use it, is to install it with the **fred-manager** script.
The manager installs the whole *FRED server* including all accessories.

Installation
============

Webwhois can be installed and run separately as any other Django application.

Instructions for custom installation:

1. Install ``webwhois``

   .. code:: shell

       python setup.py install

2. Add ``webwhois.apps.WebwhoisAppConfig`` to the ``INSTALLED_APPS`` in your ``settings.py``.

3. Link ``webwhois`` URLs into your ``urls.py``:

   .. code:: python

       from django.urls import include, path

       urlpatterns += [
           path('whois/', include('webwhois.urls')),
       ]

Settings
========

The following settings can be defined in your ``settings.py``.

``WEBWHOIS_CDNSKEY_NETLOC``
---------------------------

Network location, i.e. host and port, of the cdnskey processor server.
Default value is ``None``, i.e. scan results are not available.

``WEBWHOIS_CDNSKEY_SSL_CERT``
-----------------------------

Path to file with SSL root certificate.
Default value is ``None``, which disables the SSL encryption.

``WEBWHOIS_CORBA_NETLOC``
-------------------------

Network location, i.e. host and port, of the CORBA server.
Used to construct Interoperable Object Reference (IOR).
Default value is either ``FRED_WEBWHOIS_NETLOC`` environment variable or ``localhost``.

Example::

    WEBWHOIS_CORBA_NETLOC= 'localhost:12345'

``WEBWHOIS_CORBA_CONTEXT``
--------------------------

The ``WEBWHOIS_CORBA_CONTEXT`` variable contains a name of the CORBA context.

Example::

    WEBWHOIS_CORBA_CONTEXT = 'fred'

Default value::

    'fred'

``WEBWHOIS_LOGGER``
-------------------

A dotted path to the logger client.
Default value is ``grill.DummyLoggerClient``.

``WEBWHOIS_LOGGER_OPTIONS``
---------------------------

A mapping with options for the ``WEBWHOIS_LOGGER``.
If the key ``credentials`` is present, it will be passed to the ``make_credentials`` utility as a mapping.
Default value is ``{}``.

``WEBWHOIS_REGISTRY_NETLOC``
----------------------------

Network location, i.e. host and port, of the registry server.
This setting is required.

``WEBWHOIS_REGISTRY_SSL_CERT``
------------------------------

Path to file with SSL root certificate.
Default value is ``None``, which disables the SSL encryption.

``WEBWHOIS_SECRETARY_AUTH``
---------------------------

Object managing authentication for the django-secretary API.
For possible values see https://docs.python-requests.org/en/latest/user/authentication/.
Default value is ``None``, i.e. no authentication.

``WEBWHOIS_SECRETARY_TIMEOUT``
------------------------------

A timeout for connection to django-secretary service.
For possible values see documentation of ``requests`` library.
Default value is ``3.05``.

``WEBWHOIS_SECRETARY_URL``
--------------------------

URL of django-secretary service API.
This setting is required.

Docker
======

Webwhois can be deployed using docker.

To build image use::

    docker build --tag webwhois --file docker/uwsgi/Dockerfile .

The image provides a uWSGI service at port 16000 and a volume with static files.
Running the image requires setting a ``SECRET_KEY`` and ``ALLOWED_HOSTS`` enviroment variables.
Webwhois settings can be provided as enviroment variables as well.

.. _FRED: https://fred.nic.cz/
