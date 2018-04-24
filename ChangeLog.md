## 1.13 (2018-04-18) ##

 * Add personal info public request
 * Refactor public request responses
 * Drop support for old IDL structures
 * Remove CZ.NIC specific code - public request descriptions, dobradomena and registrar links.
 * Clean up code - pyfco deprecation warnings
 * Support omniidl up to 4.2.2
 * Use tox for testing

## 1.12.2 (2018-04-24) ##

 * Fix detail of ENUM domains.

## 1.12.1 (2018-04-17) ##

 * Fix response for domains in delete candidate status.

## 1.12 (2018-03-08) ##

 * Prepare for Python 3 - clean up code and use ``unicode_literals``.
 * Support new ISO date time and buffer structures from IDLs.
 * Handle new ``OBJECT_DELETE_CANDIDATE`` exception.
 * Use ``Babel`` for package distribution.
 * Remove mojeid contact view.
 * Move whois form to webwhois index.
 * Fix up tests.
 * Fix RPM builds.

## 1.11 (2018-02-12) ##

 * Add changelog
 * Use `setuptools` for packaging
 * Drop example `webwhois_site`
 * Define constants for statuses.
 * Handle delete candidate objects.
