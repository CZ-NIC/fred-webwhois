from __future__ import unicode_literals

from enum import Enum, unique

import six
from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.functional import lazy
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy, ugettext_lazy as _
from fred_idl.Registry.PublicRequest import ConfirmedBy

LOCK_TYPE_TRANSFER = "transfer"
LOCK_TYPE_ALL = "all"
LOCK_TYPE_URL_PARAM = "lock_type"

LOCK_TYPE = (
    (LOCK_TYPE_TRANSFER, _("transfer object")),
    (LOCK_TYPE_ALL, _("all object changes")),
)

SEND_TO_IN_REGISTRY = 'email_in_registry'
SEND_TO_CUSTOM = 'custom_email'


@unique
class ConfirmationMethod(str, Enum):
    """Enum of public request confirmation methods."""

    SIGNED_EMAIL = 'signed_email'
    NOTARIZED_LETTER = 'notarized_letter'


CONFIRMATION_METHOD_IDL_MAP = {ConfirmationMethod.SIGNED_EMAIL: ConfirmedBy.signed_email,
                               ConfirmationMethod.NOTARIZED_LETTER: ConfirmedBy.notarized_letter}


class PublicRequestBaseForm(forms.Form):
    """Base class for public request forms.

    @cvar CONFIRMATION_METHOD_CHOICES: Choices for `confirmation_method` field.
    """

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
    )
    # Deprecated attribute kept for backward compatibility
    CONFIRMATION_METHOD = CONFIRMATION_METHOD_CHOICES

    object_type = forms.ChoiceField(label=_("Object type"), choices=REGISTRY_OBJECT_TYPE)
    handle = forms.CharField(
        label=lazy(lambda: mark_safe(_("Domain (without <em>www.</em> prefix) / Handle")), six.text_type)(),
        validators=[MaxLengthValidator(255)])
    confirmation_method = forms.ChoiceField(label=_("Confirmation method"), choices=CONFIRMATION_METHOD_CHOICES,
                                            required=False)

    def clean_confirmation_method(self):
        """Return None if no confirmation method was selected."""
        value = self.cleaned_data['confirmation_method']
        if value:
            return value
        else:
            return None


class SendPasswordForm(PublicRequestBaseForm):
    """Send password for transfer."""

    SEND_TO = (
        (SEND_TO_IN_REGISTRY, _('email in registry')),
        (SEND_TO_CUSTOM, _('custom email')),
    )
    send_to = forms.ChoiceField(choices=SEND_TO, initial=SEND_TO_IN_REGISTRY, widget=forms.RadioSelect,
                                label=_("Send to"))
    custom_email = forms.EmailField(label=_("Custom email"), required=False)
    field_order = ('object_type', 'handle', 'send_to', 'custom_email', 'confirmation_method')

    def clean(self):
        cleaned_data = super(SendPasswordForm, self).clean()
        if cleaned_data.get('send_to') == SEND_TO_IN_REGISTRY:
            if cleaned_data.get('custom_email'):
                raise forms.ValidationError(_(
                    'Option "Send to email in registry" is incompatible with custom email. Please choose one of '
                    'the two options.'), code='unexpected_custom_email')
        elif cleaned_data.get('send_to') == SEND_TO_CUSTOM:
            if not cleaned_data.get('custom_email'):
                raise forms.ValidationError(_('Custom email is required as "Send to custom email" option is selected.'
                                              ' Please fill it in.'), code='custom_email_missing')

        if cleaned_data.get('confirmation_method') == ConfirmationMethod.NOTARIZED_LETTER \
                and cleaned_data.get('send_to') != 'custom_email':
            raise forms.ValidationError(_('Letter with officially verified signature can be sent only to the custom '
                                          'email. Please select "Send to custom email" and enter it.'),
                                        code='custom_email_required')


class PersonalInfoForm(SendPasswordForm):
    """Form for public request for personal info."""

    object_type = None
    handle = forms.CharField(label=_("Contact handle"), validators=[MaxLengthValidator(255)])


class BlockObjectForm(PublicRequestBaseForm):
    """Block object in registry."""

    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Block"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')


class UnblockObjectForm(PublicRequestBaseForm):
    """Unblock object in registry."""

    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Unblock"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')
