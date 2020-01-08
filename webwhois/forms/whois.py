#
# Copyright (C) 2015-2020  CZ.NIC, z. s. p. o.
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
from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class WhoisForm(forms.Form):
    """Whois form to enter HANDLE."""

    handle = forms.CharField(
        label=lazy(lambda: mark_safe(_("Domain (without <em>www.</em> prefix) / Handle")), str)(),
        required=True, validators=[MaxLengthValidator(255)],
    )
