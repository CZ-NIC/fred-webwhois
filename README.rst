========
Webwhois
========

The **Webwhois** is a Django application with the Whois service for the FRED registry system.
The application searches domain names, contacts, nameserver sets and key sets.


Dependencies
============

- python 2.7
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

2. Add ``webwhois`` to the ``INSTALLED_APPS`` in your ``settings.py``.

3. Link ``webwhois`` URLs into your ``urls.py``:

   .. code:: python

       urlpatterns += [
           url(r'^whois', include('webwhois.urls')),
       ]

Settings
========

The following settings can be defined in your ``settings.py``.

CORBA settings
--------------

CORBA variables are required to establish a connection to the **FRED server** instance.

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

The ``WEBWHOIS_LOGGER`` variable contains definition for import logger object. It can be ``None``.

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


Search engines settings
-----------------------

Information about search engines. It is a list of engines for searching domain
names in zones that are not managed by *FRED*. They are displayed
on the "Search in Registry" form page.

``WEBWHOIS_SEARCH_ENGINES``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_SEARCH_ENGINES`` variable contains a list of dictionaries with values
required for displaying links. Each dictionary contains keys: ``label`` for link label
and ``href`` for link attribute *href*.

Example::

    WEBWHOIS_SEARCH_ENGINES = (
        {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
        {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
    )

Default value::

    (
        {"label": "WHOIS.COM Lookup", "href": "http://www.whois.com/whois/"},
        {"label": "IANA WHOIS Service", "href": "http://www.iana.org/whois"},
    )


Registrars settings
-------------------

Information about registrars. There are links displayed on the page with a list of registrars.

``WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL`` variable contains a link to the description
"How to become a registrar".

Example::

    WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL = "https://www.nic.cz/page/309/how-to-become-a-registrar-/"

Default value::

    None

``WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL`` variable contains a link to the page with the list of registrars.

Example::

    WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL = "https://www.nic.cz/page/928/"

Default value::

    None

``WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC`` variable contains a link to the page with the specific content related to
the subject.

Example::

    WEBWHOIS_REGISTRAR_SUPPORTS_DNSSEC = "https://www.nic.cz/page/928/#dnssec"

Default value::

    None

``WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID`` variable contains a link to the page with the specific content related to
the subject.

Example::

    WEBWHOIS_REGISTRAR_SUPPORTS_MOJEID = "https://www.nic.cz/page/928/#mojeid"

Default value::

    None

``WEBWHOIS_REGISTRAR_SUPPORTS_IPV6``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRAR_SUPPORTS_IPV6`` variable contains a link to the page with the specific content related to
the subject.

Example::

    WEBWHOIS_REGISTRAR_SUPPORTS_IPV6 = "https://www.nic.cz/page/928/#ipv6"

Default value::

    None

``WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED`` variable contains a code that represents certified registrars in the registry.
The certified registrars are shown in the list "Registrars offering also retail services".

Example::

    WEBWHOIS_REGISTRARS_GROUPS_CERTIFIED = ["certified"]

Default value::

    []

``WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED`` variable contains a code that represents uncertified registrars in the registry.
The uncertified registrars are shown in the list "Registrars offering only wholesale services".

Example::

    WEBWHOIS_REGISTRARS_GROUPS_UNCERTIFIED = ["uncertified"]

Default value::

    []


DNSSEC settings
---------------

Information about the DNSSEC system. There is a link displayed on the page above the list of registrars.

``WEBWHOIS_DNSSEC_URL``
^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_DNSSEC_URL`` variable containts a link to the page describing the system. It can be ``None``.

Example::

    WEBWHOIS_DNSSEC_URL = "http://www.nic.cz/dnssec/"

Default value::

    None


``WEBWHOIS_HOW_TO_REGISTER_LINK``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``WEBWHOIS_HOW_TO_REGISTER_LINK`` variable contains a dictionary with items for URL.
The dictionary contains keys ``label`` for link label and ``href`` for link attribute *href*.
The link is displayed on the page as a clue in case the object was not found in the registry.

Example::

    WEBWHOIS_HOW_TO_REGISTER_LINK = {
        "href": "http://www.dobradomena.cz/",
        "label": "www.dobradomena.cz"
    }

Default value::

    None


The schema of integration into a project
========================================

The schema is shown on the main page of the standalone site.

.. image:: docs/webwhois-integration-schema.svg

.. _FRED: https://fred.nic.cz/
