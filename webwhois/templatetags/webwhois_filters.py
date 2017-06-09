import re
import textwrap

import idna
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import ugettext_lazy as _

register = template.Library()


@register.filter
def text_wrap(value, size):
    """Insert enters (LF) into the text on every position defined by the size. Value must not be None."""
    return "\n".join(textwrap.wrap(value, size))


SSN_TYPE = {
    'RC':       _('Birth date'),
    'OP':       _('Personal ID'),
    'PASS':     _('Passport number'),
    'ICO':      _('VAT ID number'),
    'MPSV':     _('MPSV ID'),
    'BIRTHDAY': _('Birth day'),
}


@register.filter
@stringfilter
def contact_ssn_type_label(value):
    """Replace SSN type code by translated description."""
    return SSN_TYPE.get(value, u"%s: %s" % (_('Unspecified type'), value)) if value else ''


@register.filter
@stringfilter
def idn_decode(value):
    """Decode handle into IDN."""
    try:
        return idna.decode(value)
    except idna.IDNAError:
        pass
    return value


@register.filter
@stringfilter
def add_scheme(value):
    """Add scheme (protocol) when missing in url."""
    if not re.match("https?://", value):
        return "http://" + value
    return value


@register.filter
@stringfilter
def strip_scheme(value):
    """Strip scheme (protocol) from url."""
    return re.sub("^https?://", "", value)
