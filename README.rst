========
Webwhois
========

The **Webwhois** is a Django application with the Whois service for the FRED registry system.
The application searches domain names, contacts, nameserver sets and key sets.


Dependencies
============

- python >=3.6
- Other dependencies are listed in `<requirements.txt>`_.


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
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Network location, i.e. host and port, of the cdnskey processor server.
Default value is ``None``, i.e. scan results are not available.

``WEBWHOIS_CDNSKEY_SSL_CERT``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Path to file with SSL root certificate.
Default value is ``None``, which disables the SSL encryption.

``WEBWHOIS_CORBA_NETLOC``
^^^^^^^^^^^^^^^^^^^^^^^^^

Network location, i.e. host and port, of the CORBA server.
Used to construct Interoperable Object Reference (IOR).
Default value is either ``FRED_WEBWHOIS_NETLOC`` environment variable or ``localhost``.

Example::

    WEBWHOIS_CORBA_NETLOC= 'localhost:12345'

``WEBWHOIS_CORBA_CONTEXT``
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_CORBA_CONTEXT`` variable contains a name of the CORBA context.

Example::

    WEBWHOIS_CORBA_CONTEXT = 'fred'

Default value::

    'fred'

``WEBWHOIS_LOGGER``
^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_LOGGER`` variable contains dotted path to a logger class.
If ``None``, logging to logger will be disabled.

Example::

    WEBWHOIS_LOGGER = 'pylogger.corbalogger.LoggerFailSilent'

Default value::

    'pylogger.corbalogger.Logger'

``WEBWHOIS_LOGGER_CORBA_NETLOC``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Network location, i.e. host and port, of the CORBA server for logging.
Used to construct Interoperable Object Reference (IOR).
By default a ``WEBWHOIS_CORBA_NETLOC`` is used.

``WEBWHOIS_LOGGER_CORBA_CONTEXT``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_LOGGER_CORBA_CONTEXT`` variable contains a name of the Logger CORBA context. This is usually same as
a **Fred CORBA** instance.

Example::

    WEBWHOIS_LOGGER_CORBA_CONTEXT = WEBWHOIS_CORBA_CONTEXT

Default value::

    WEBWHOIS_CORBA_CONTEXT

``WEBWHOIS_LOGGER_CORBA_OBJECT``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The name of the CORBA object for logger.
Default value is ``Logger``.

Docker
======

Webwhois can be deployed using docker.

To build image use::

    docker build --tag webwhois --file docker/uwsgi/Dockerfile .

The image provides a uWSGI service at port 16000 and a volume with static files.
Running the image requires setting a ``SECRET_KEY`` and ``ALLOWED_HOSTS`` enviroment variables.
Webwhois settings can be provided as enviroment variables as well.

.. _FRED: https://fred.nic.cz/
