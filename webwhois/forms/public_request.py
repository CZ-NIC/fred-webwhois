#
# Copyright (C) 2017-2022  CZ.NIC, z. s. p. o.
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
#
from enum import Enum, unique
from typing import Dict

from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, pgettext_lazy
from fred_idl.Registry.PublicRequest import ConfirmedBy

from ..constants import SEND_TO_CUSTOM, SEND_TO_IN_REGISTRY, PublicRequestsLogEntryType
from .fields import DeliveryField
from .widgets import DeliveryType

LOCK_TYPE_TRANSFER = "transfer"
LOCK_TYPE_ALL = "all"
LOCK_TYPE_URL_PARAM = "lock_type"

LOCK_TYPE = (
    (LOCK_TYPE_TRANSFER, _("object transfer")),
    (LOCK_TYPE_ALL, _("all object changes")),
)


@unique
class ConfirmationMethod(str, Enum):
    """Enum of public request confirmation methods."""

    SIGNED_EMAIL = 'signed_email'
    NOTARIZED_LETTER = 'notarized_letter'
    GOVERNMENT = 'government'


CONFIRMATION_METHOD_IDL_MAP = {ConfirmationMethod.SIGNED_EMAIL: ConfirmedBy.signed_email,
                               ConfirmationMethod.NOTARIZED_LETTER: ConfirmedBy.notarized_letter,
                               ConfirmationMethod.GOVERNMENT: ConfirmedBy.government}


class PublicRequestBaseForm(forms.Form):
    """Base class for public request forms.

    @cvar CONFIRMATION_METHOD_CHOICES: Choices for `confirmation_method` field.
    """

    log_entry_type: PublicRequestsLogEntryType

    REGISTRY_OBJECT_TYPE = (
        ("domain", _("Domain")),
        ("contact", _("Contact")),
        ("nsset", _("Nsset")),
        ("keyset", _("Keyset")),
    )
    CONFIRMATION_METHOD_CHOICES = (
        # Forms work best with strings. Use raw enum values, not enum objects.
        (ConfirmationMethod.SIGNED_EMAIL.value, _("Email signed by a qualified certificate")),
        (ConfirmationMethod.NOTARIZED_LETTER.value, _("Officially verified signature")),
        (ConfirmationMethod.GOVERNMENT.value, _("E-government")),
    )

    object_type = forms.ChoiceField(label=_("Object type"), choices=REGISTRY_OBJECT_TYPE)
    handle = forms.CharField(
        label=lazy(lambda: mark_safe(_("Domain (without <em>www.</em> prefix) / Handle")), str)(),
        validators=[MaxLengthValidator(255)])
    confirmation_method = forms.ChoiceField(label=_("Confirmation method"), choices=CONFIRMATION_METHOD_CHOICES,
                                            required=False,
                                            help_text=_('If you are entering another e-mail, you must attach '
                                            'verification that entered e-mail belongs to the responsible person.'))

    def clean_confirmation_method(self):
        """Return None if no confirmation method was selected."""
        value = self.cleaned_data['confirmation_method']
        if value:
            return value
        else:
            return None

    def get_log_properties(self) -> Dict[str, str]:
        """Return properties for log."""
        properties = {"handle": self.cleaned_data["handle"]}
        if 'object_type' in self.cleaned_data:
            properties["handleType"] = self.cleaned_data['object_type']
        if self.cleaned_data['confirmation_method']:
            properties["confirmMethod"] = self.cleaned_data['confirmation_method']
        return properties


class SendPasswordForm(PublicRequestBaseForm):
    """Send password for transfer."""

    log_entry_type = PublicRequestsLogEntryType.AUTH_INFO

    SEND_TO = (
        (SEND_TO_IN_REGISTRY, _('email in registry')),
        (SEND_TO_CUSTOM, _('custom email')),
    )

    send_to = DeliveryField(choices=SEND_TO, initial=DeliveryType(SEND_TO_IN_REGISTRY, ""), label=_("Send to"))

    field_order = ('object_type', 'handle', 'send_to', 'confirmation_method')

    def clean(self):
        cleaned_data = self.cleaned_data

        confirmation_method = cleaned_data.get('confirmation_method')
        if confirmation_method is not None and confirmation_method != ConfirmationMethod.SIGNED_EMAIL \
                and 'send_to' in cleaned_data and cleaned_data.get('send_to').choice != SEND_TO_CUSTOM:
            raise forms.ValidationError(_('Letter with officially verified signature can be sent only to the custom '
                                          'email. Please select "Send to custom email" and enter it.'),
                                        code='custom_email_required')

        return cleaned_data

    def get_log_properties(self) -> Dict[str, str]:
        """Return properties for log."""
        properties = super().get_log_properties()
        properties["sendTo"] = self.cleaned_data['send_to'].choice
        if self.cleaned_data['send_to'].custom_email:
            properties["customEmail"] = self.cleaned_data['send_to'].custom_email
        return properties


class PersonalInfoForm(SendPasswordForm):
    """Form for public request for personal info."""

    log_entry_type = PublicRequestsLogEntryType.PERSONAL_INFO

    object_type = None
    handle = forms.CharField(label=_("Contact handle"), validators=[MaxLengthValidator(255)])

    def get_log_properties(self) -> Dict[str, str]:
        """Return properties for log."""
        properties = super().get_log_properties()
        properties["handleType"] = "contact"
        return properties


class BlockObjectForm(PublicRequestBaseForm):
    """Block object in registry."""

    confirmation_method = forms.ChoiceField(label=_("Confirmation method"), required=False,
                                            choices=PublicRequestBaseForm.CONFIRMATION_METHOD_CHOICES,
                                            help_text=_('You must attach that request is applied by the responsible '
                                            'person.'))

    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Block"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')

    _LOG_ENTRY_TYPES = {
        LOCK_TYPE_TRANSFER: PublicRequestsLogEntryType.BLOCK_TRANSFER,
        LOCK_TYPE_ALL: PublicRequestsLogEntryType.BLOCK_CHANGES,
    }

    @property
    def log_entry_type(self) -> PublicRequestsLogEntryType:  # type: ignore[override]
        """Return a log entry type."""
        return self._LOG_ENTRY_TYPES[self.cleaned_data['lock_type']]


class UnblockObjectForm(PublicRequestBaseForm):
    """Unblock object in registry."""

    confirmation_method = forms.ChoiceField(label=_("Confirmation method"), required=False,
                                            choices=PublicRequestBaseForm.CONFIRMATION_METHOD_CHOICES,
                                            help_text=_('You must attach that request is applied by the responsible '
                                            'person.'))

    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Unblock"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')

    _LOG_ENTRY_TYPES = {
        LOCK_TYPE_TRANSFER: PublicRequestsLogEntryType.UNBLOCK_TRANSFER,
        LOCK_TYPE_ALL: PublicRequestsLogEntryType.UNBLOCK_CHANGES,
    }

    @property
    def log_entry_type(self) -> PublicRequestsLogEntryType:  # type: ignore[override]
        """Return a log entry type."""
        return self._LOG_ENTRY_TYPES[self.cleaned_data['lock_type']]
