#
# Copyright (C) 2015-2021  CZ.NIC, z. s. p. o.
#
# This file is part of FRED.
#
# FRED is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FRED is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FRED.  If not, see <https://www.gnu.org/licenses/>.
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
    'RC': _('Day of Birth'),
    'OP': _('ID card number'),
    'PASS': _('Passport number'),
    'ICO': _('VAT ID number'),
    'MPSV': _('MPSV ID'),
    'BIRTHDAY': _('Day of Birth'),
}


@register.filter
@stringfilter
def contact_ssn_type_label(value):
    """Replace SSN type code by translated description."""
    return SSN_TYPE.get(value, "%s: %s" % (_('Unspecified type'), value)) if value else ''


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
