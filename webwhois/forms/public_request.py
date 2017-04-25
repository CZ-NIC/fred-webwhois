from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.translation import pgettext_lazy, ugettext_lazy as _

from .fields import RemoveWhitespacesField

LOCK_TYPE_TRANSFER = "transfer"
LOCK_TYPE_ALL = "all"
LOCK_TYPE_URL_PARAM = "lock_type"

LOCK_TYPE = (
    (LOCK_TYPE_TRANSFER, _("transfer object")),
    (LOCK_TYPE_ALL, _("all object changes")),
)

SEND_TO_IN_REGISTRY = 'email_in_registry'
SEND_TO_CUSTOM = 'custom_email'


class PublicRequestBaseForm(forms.Form):

    REGISTRY_OBJECT_TYPE = (
        ("domain", _("Domain")),
        ("contact", _("Contact")),
        ("nsset", _("Nsset")),
        ("keyset", _("Keyset")),
    )
    CONFIRMATION_METHOD = (
        ("signed_email", _("Email signed by a qualified certificate")),
        ("notarized_letter", _("Officially verified signature")),
    )

    object_type = forms.ChoiceField(label=_("Object type"), choices=REGISTRY_OBJECT_TYPE)
    handle = RemoveWhitespacesField(label=_("Handle"), validators=[MaxLengthValidator(255)])
    confirmation_method = forms.ChoiceField(label=_("Confirmation method"), choices=CONFIRMATION_METHOD, required=False)


class SendPasswordForm(PublicRequestBaseForm):
    "Send password for transfer."
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

        if cleaned_data.get('confirmation_method') == 'notarized_letter' \
                and cleaned_data.get('send_to') != 'custom_email':
            raise forms.ValidationError(_('Letter with officially verified signature can be sent only to the custom '
                                          'email. Please select "Send to custom email" and enter it.'),
                                        code='custom_email_required')


class BlockObjectForm(PublicRequestBaseForm):
    "Block object in registry."
    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Block"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')


class UnblockObjectForm(PublicRequestBaseForm):
    "Unblock object in registry."
    lock_type = forms.ChoiceField(choices=LOCK_TYPE, initial=LOCK_TYPE_TRANSFER, widget=forms.RadioSelect,
                                  label=pgettext_lazy("verb_inf", "Unblock"))
    field_order = ('lock_type', 'object_type', 'handle', 'confirmation_method')
