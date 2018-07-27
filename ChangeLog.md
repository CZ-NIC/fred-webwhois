## 1.14 (2018-07-27) ##

 * Add Python 3 and Django 2.0 support.
 * Improve behaviour of confirmation methods in public requests.
 * Add public response object to context of public response views.
 * Add government confirmation method for public requests.
 * Fix wording of error message in personal info public request.
 * Fix unmanaged zone behaviour.
 * Remove status codes from HTML data attributes.
 * Remove public response backports.
 * Remove links for search engines and domain registration from settings and templates.
 * Remove ``webwhois_base_template`` attribute from views. Use ``base_template`` instead.
 * Remove CZ.NIC specific webwhois templates.
 * Remove obsolete ``default_app_config``.
 * Fix Fedora builds.

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
