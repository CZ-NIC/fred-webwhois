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
import logging
from typing import Any, Dict, Optional, Type

from django.core.cache import cache
from django.forms import Form
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.formats import date_format
from django.utils.html import format_html
from django.utils.translation import get_language, gettext_lazy as _
from django.views.generic import TemplateView, View
from fred_idl.Registry.PublicRequest import (HAS_DIFFERENT_BLOCK, INVALID_EMAIL, OBJECT_ALREADY_BLOCKED,
                                             OBJECT_NOT_BLOCKED, OBJECT_NOT_FOUND, OBJECT_TRANSFER_PROHIBITED,
                                             OPERATION_PROHIBITED, Language, LockRequestType)

from webwhois.forms import BlockObjectForm, PersonalInfoForm, SendPasswordForm, UnblockObjectForm
from webwhois.forms.public_request import (CONFIRMATION_METHOD_IDL_MAP, LOCK_TYPE_ALL, LOCK_TYPE_TRANSFER,
                                           LOCK_TYPE_URL_PARAM, SEND_TO_CUSTOM, SEND_TO_IN_REGISTRY, ConfirmationMethod)
from webwhois.forms.widgets import DeliveryType
from webwhois.utils.corba_wrapper import LOGGER, PUBLIC_REQUEST
from webwhois.utils.public_response import BlockResponse, PersonalInfoResponse, SendPasswordResponse
from webwhois.views.base import BaseContextMixin
from webwhois.views.public_request_mixin import (PublicRequestFormView, PublicRequestKnownException,
                                                 PublicRequestLoggerMixin)

WEBWHOIS_LOGGING = logging.getLogger(__name__)


class SendPasswordFormView(BaseContextMixin, PublicRequestFormView):
    """Send password (AuthInfo) view."""

    form_class = SendPasswordForm
    template_name = 'webwhois/form_send_password.html'
    form_cleaned_data = None  # type: Dict[str, Any]

    def _get_logging_request_name_and_properties(self, data):
        """Return Request type name and Properties."""
        properties_in = [
            ("handle", data["handle"]),
            ("handleType", data['object_type']),
            ("sendTo", data['send_to'].choice),
        ]
        if data['confirmation_method']:
            properties_in.append(("confirmMethod", data['confirmation_method']))
        custom_email = data.get("send_to").custom_email
        if custom_email:
            properties_in.append(("customEmail", custom_email))
        return "AuthInfo", properties_in

    def _call_registry_command(self, form, log_request_id):
        data = form.cleaned_data
        try:
            if data['send_to'].choice == 'custom_email':
                response_id = PUBLIC_REQUEST.create_authinfo_request_non_registry_email(
                    self._get_object_type(data['object_type']), data['handle'], log_request_id,
                    CONFIRMATION_METHOD_IDL_MAP[data['confirmation_method']], data['send_to'].custom_email)
            else:
                # confirm_type_name is 'signed_email'
                response_id = PUBLIC_REQUEST.create_authinfo_request_registry_email(
                    self._get_object_type(data['object_type']), data['handle'], log_request_id)
        except OBJECT_NOT_FOUND as err:
            form.add_error('handle',
                           _('Object not found. Check that you have correctly entered the Object type and Handle.'))
            raise PublicRequestKnownException(type(err).__name__)
        except OBJECT_TRANSFER_PROHIBITED as err:
            form.add_error('handle', _('Transfer of object is prohibited. The request can not be accepted.'))
            raise PublicRequestKnownException(type(err).__name__)
        except INVALID_EMAIL as err:
            form.add_error('send_to', _('The email was not found or the address is not valid.'))
            raise PublicRequestKnownException(type(err).__name__)
        return response_id

    def get_public_response(self, form, public_request_id):
        request_type = self._get_logging_request_name_and_properties(form.cleaned_data)[0]
        if form.cleaned_data['send_to'].choice == 'custom_email':
            custom_email = form.cleaned_data['send_to'].custom_email
        else:
            custom_email = None
        return SendPasswordResponse(form.cleaned_data['object_type'], public_request_id, request_type,
                                    form.cleaned_data['handle'], custom_email, form.cleaned_data['confirmation_method'])

    def get_initial(self):
        data = super(SendPasswordFormView, self).get_initial()
        data["handle"] = self.request.GET.get("handle")
        data["object_type"] = self.request.GET.get("object_type")
        send_to = self.request.GET.get("send_to")
        if send_to and send_to in (SEND_TO_IN_REGISTRY, SEND_TO_CUSTOM):
            data["send_to"] = DeliveryType(send_to, '')
        return data

    def get_success_url(self):
        if self.success_url:
            return force_str(self.success_url)
        url_name = "webwhois:response_not_found"
        if self.form_cleaned_data['send_to'].choice == 'email_in_registry':
            url_name = 'webwhois:email_in_registry_response'
        else:
            assert self.form_cleaned_data['send_to'].choice == 'custom_email'
            if self.form_cleaned_data['confirmation_method'] == ConfirmationMethod.SIGNED_EMAIL:
                url_name = 'webwhois:custom_email_response'
            else:
                url_name = 'webwhois:notarized_letter_response'
        return reverse(url_name, kwargs={'public_key': self.public_key},
                       current_app=self.request.resolver_match.namespace)


class PersonalInfoFormView(BaseContextMixin, PublicRequestFormView):
    """View to create public request for personal info."""

    form_class = PersonalInfoForm
    template_name = 'webwhois/form_personal_info.html'
    form_cleaned_data = None  # type: Dict[str, Any]

    def _get_logging_request_name_and_properties(self, data):
        """Return Request type name and Properties."""
        properties_in = [
            ("handle", data["handle"]),
            ("handleType", 'contact'),
            ("sendTo", data['send_to'].choice),
        ]
        if data['confirmation_method']:
            properties_in.append(("confirmMethod", data['confirmation_method']))
        custom_email = data.get("send_to").custom_email
        if custom_email:
            properties_in.append(("customEmail", custom_email))
        return "PersonalInfo", properties_in

    def _call_registry_command(self, form, log_request_id):
        data = form.cleaned_data
        try:
            if data['send_to'].choice == SEND_TO_CUSTOM:
                response_id = PUBLIC_REQUEST.create_personal_info_request_non_registry_email(
                    data['handle'], log_request_id, CONFIRMATION_METHOD_IDL_MAP[data['confirmation_method']],
                    data['send_to'].custom_email)
            else:
                assert data['send_to'].choice == SEND_TO_IN_REGISTRY
                response_id = PUBLIC_REQUEST.create_personal_info_request_registry_email(data['handle'], log_request_id)
        except OBJECT_NOT_FOUND as err:
            form.add_error('handle',
                           _('Object not found. Check that you have correctly entered the contact handle.'))
            raise PublicRequestKnownException(type(err).__name__)
        except INVALID_EMAIL as err:
            form.add_error('send_to', _('The email was not found or the address is not valid.'))
            raise PublicRequestKnownException(type(err).__name__)
        return response_id

    def get_public_response(self, form, public_request_id):
        request_type = self._get_logging_request_name_and_properties(form.cleaned_data)[0]
        if form.cleaned_data['send_to'].choice == 'custom_email':
            custom_email = form.cleaned_data['send_to'].custom_email
        else:
            custom_email = None
        return PersonalInfoResponse('contact', public_request_id, request_type, form.cleaned_data['handle'],
                                    custom_email, form.cleaned_data['confirmation_method'])

    def get_success_url(self):
        if self.success_url:
            return force_str(self.success_url)
        if self.form_cleaned_data['send_to'].choice == 'email_in_registry':
            url_name = 'webwhois:email_in_registry_response'
        else:
            assert self.form_cleaned_data['send_to'].choice == 'custom_email'
            if self.form_cleaned_data['confirmation_method'] == ConfirmationMethod.SIGNED_EMAIL:
                url_name = 'webwhois:custom_email_response'
            else:
                url_name = 'webwhois:notarized_letter_response'
        return reverse(url_name, kwargs={'public_key': self.public_key},
                       current_app=self.request.resolver_match.namespace)


class BlockUnblockFormView(PublicRequestFormView):
    """Block or Unblock object form view."""

    form_class = None  # type: Type[Form]
    block_action = None  # type: str
    logging_lock_type = None  # type: Dict[str, str]
    form_cleaned_data = None  # type: Dict[str, Any]

    def _get_lock_type(self, key):
        raise NotImplementedError

    def _get_logging_request_name_and_properties(self, data):
        """Return Request type name and Properties."""
        lock_type_key = self.logging_lock_type[data['lock_type']]
        properties_in = [
            ("handle", data["handle"]),
            ("handleType", data['object_type']),
        ]
        if data['confirmation_method']:
            properties_in.append(("confirmMethod", data['confirmation_method']))
        return lock_type_key, properties_in

    def _call_registry_command(self, form, log_request_id):
        response_id = None
        try:
            response_id = PUBLIC_REQUEST.create_block_unblock_request(
                self._get_object_type(form.cleaned_data['object_type']), form.cleaned_data['handle'], log_request_id,
                CONFIRMATION_METHOD_IDL_MAP[form.cleaned_data['confirmation_method']],
                self._get_lock_type(form.cleaned_data['lock_type']))
        except OBJECT_NOT_FOUND as err:
            form.add_error('handle', _('Object not found. Check that you have correctly entered the Object type and '
                                       'Handle.'))
            raise PublicRequestKnownException(type(err).__name__)
        except OBJECT_ALREADY_BLOCKED as err:
            form.add_error('handle', _('This object is already blocked. The request can not be accepted.'))
            raise PublicRequestKnownException(type(err).__name__)
        except OBJECT_NOT_BLOCKED as err:
            form.add_error('handle', _('This object is not blocked. The request can not be accepted.'))
            raise PublicRequestKnownException(type(err).__name__)
        except HAS_DIFFERENT_BLOCK as err:
            form.add_error('handle', _('This object has another active blocking. The request can not be accepted.'))
            raise PublicRequestKnownException(type(err).__name__)
        except OPERATION_PROHIBITED as err:
            form.add_error('handle', _('Operation for this object is prohibited. The request can not be accepted.'))
            raise PublicRequestKnownException(type(err).__name__)
        return response_id

    def get_public_response(self, form, public_request_id):
        request_type = self._get_logging_request_name_and_properties(form.cleaned_data)[0]
        return BlockResponse(form.cleaned_data['object_type'], public_request_id, request_type,
                             form.cleaned_data['handle'], self.block_action, form.cleaned_data['lock_type'],
                             form.cleaned_data['confirmation_method'])

    def get_initial(self):
        data = super(BlockUnblockFormView, self).get_initial()
        data["handle"] = self.request.GET.get("handle")
        data["object_type"] = self.request.GET.get("object_type")
        lock_type = self.request.GET.get(LOCK_TYPE_URL_PARAM)
        if lock_type and lock_type in (LOCK_TYPE_TRANSFER, LOCK_TYPE_ALL):
            data["lock_type"] = lock_type
        return data

    def get_success_url(self):
        if self.success_url:
            return force_str(self.success_url)
        if self.form_cleaned_data['confirmation_method'] == ConfirmationMethod.SIGNED_EMAIL:
            url_name = 'webwhois:custom_email_response'
        else:
            url_name = 'webwhois:notarized_letter_response'
        return reverse(url_name, kwargs={'public_key': self.public_key},
                       current_app=self.request.resolver_match.namespace)


class BlockObjectFormView(BaseContextMixin, BlockUnblockFormView):
    """Block object form view."""

    form_class = BlockObjectForm
    template_name = 'webwhois/form_block_object.html'
    block_action = 'block'
    logging_lock_type = {
        LOCK_TYPE_TRANSFER: "BlockTransfer",
        LOCK_TYPE_ALL: "BlockChanges",
    }

    def _get_lock_type(self, key):
        return {
            LOCK_TYPE_TRANSFER: LockRequestType.block_transfer,
            LOCK_TYPE_ALL: LockRequestType.block_transfer_and_update,
        }[key]


class UnblockObjectFormView(BaseContextMixin, BlockUnblockFormView):
    """Unblock object form view."""

    form_class = UnblockObjectForm
    template_name = 'webwhois/form_unblock_object.html'
    block_action = 'unblock'
    logging_lock_type = {
        LOCK_TYPE_TRANSFER: "UnblockTransfer",
        LOCK_TYPE_ALL: "UnblockChanges",
    }

    def _get_lock_type(self, key):
        return {
            LOCK_TYPE_TRANSFER: LockRequestType.unblock_transfer,
            LOCK_TYPE_ALL: LockRequestType.unblock_transfer_and_update,
        }[key]


class PublicResponseNotFound(Exception):
    """Public response was not found in the cache."""


class PublicResponseNotFoundView(BaseContextMixin, TemplateView):
    """Response Not found view."""

    template_name = 'webwhois/public_request_response_not_found.html'


class BaseResponseTemplateView(BaseContextMixin, TemplateView):
    """Base view for public request responses."""

    def __init__(self, *args, **kwargs):
        super(BaseResponseTemplateView, self).__init__(*args, **kwargs)
        self._public_response = None

    def get(self, request, *args, **kwargs):
        try:
            self.get_public_response()
        except PublicResponseNotFound:
            return HttpResponseRedirect(reverse("webwhois:response_not_found",
                                                kwargs={"public_key": kwargs['public_key']},
                                                current_app=self.request.resolver_match.namespace))
        return super(BaseResponseTemplateView, self).get(request, *args, **kwargs)

    def get_public_response(self):
        """Return relevant public response."""
        # Cache the result for case the cache gets deleted while handling the request.
        if self._public_response is None:
            public_key = self.kwargs['public_key']
            public_response = cache.get(public_key)
            if public_response is None:
                raise PublicResponseNotFound(public_key)
            self._public_response = public_response
        return self._public_response

    def get_context_data(self, **kwargs):
        """Add public response object to the context."""
        context = super(BaseResponseTemplateView, self).get_context_data(**kwargs)
        context.setdefault('public_response', self.get_public_response())
        return context


class TextSendPasswordMixin(object):
    """Texts shared by all Request for password response views."""

    text_title = {
        'contact': _('Request to send a password (authinfo) for transfer contact %(handle)s'),
        'domain': _('Request to send a password (authinfo) for transfer domain name %(handle)s'),
        'nsset': _('Request to send a password (authinfo) for transfer nameserver set %(handle)s'),
        'keyset': _('Request to send a password (authinfo) for transfer keyset %(handle)s'),
    }


class EmailInRegistryView(TextSendPasswordMixin, BaseResponseTemplateView):
    """Email in registy view."""

    template_name = 'webwhois/public_request_email_in_registry.html'

    text_content = {
        'contact': _('We received successfully your request for a password to change the contact '
                     '<strong>{handle}</strong> sponsoring registrar. An email with the password will be sent '
                     'to the email address from the registry.'),
        'domain': _('We received successfully your request for a password to change the domain '
                    '<strong>{handle}</strong> sponsoring registrar. An email with the password will be sent '
                    'to the email address of domain holder and admin contacts.'),
        'nsset': _('We received successfully your request for a password to change the nameserver set '
                   '<strong>{handle}</strong> sponsoring registrar. An email with the password will be sent '
                   'to the email addresses of the nameserver set\'s technical contacts.'),
        'keyset': _('We received successfully your request for a password to change the keyset '
                    '<strong>{handle}</strong> sponsoring registrar. An email with the password will be sent '
                    'to the email addresses of the keyset\'s technical contacts.'),
    }
    personal_info_title = _('Request for personal data of contact %(handle)s')
    personal_info_content = _(
        'We received your request for personal data of the contact <strong>{handle}</strong> successfully. An email '
        'with the personal data will be sent to the email address from the registry.')

    def get_context_data(self, **kwargs):
        context = super(EmailInRegistryView, self).get_context_data(**kwargs)
        public_response = self.get_public_response()
        if isinstance(public_response, SendPasswordResponse):
            title = self.text_title[public_response.object_type] % {'handle': public_response.handle}
            context['text_title'] = context['text_header'] = title
            context['text_content'] = format_html(self.text_content[public_response.object_type],
                                                  handle=public_response.handle)
        else:
            assert isinstance(public_response, PersonalInfoResponse)
            title = self.personal_info_title % {'handle': public_response.handle}
            context['text_title'] = context['text_header'] = title
            context['text_content'] = format_html(self.personal_info_content, handle=public_response.handle)
        return context


class TextPasswordAndBlockMixin(TextSendPasswordMixin):
    """Texts shared by Custom e-mail view and Notarized letter view."""

    text_title = {
        'send_password': TextSendPasswordMixin.text_title,
        'personal_info': _('Request to send personal information of contact %(handle)s'),
        'block_transfer': {
            'contact': _('Request to enable enhanced object security of contact %(handle)s'),
            'domain': _('Request to enable enhanced object security of domain name %(handle)s'),
            'nsset': _('Request to enable enhanced object security of nameserver set %(handle)s'),
            'keyset': _('Request to enable enhanced object security of keyset %(handle)s'),
        },
        'block': {
            'contact': _('Request to enable enhanced object security of contact %(handle)s'),
            'domain': _('Request to enable enhanced object security of domain name %(handle)s'),
            'nsset': _('Request to enable enhanced object security of nameserver set %(handle)s'),
            'keyset': _('Request to enable enhanced object security of keyset %(handle)s'),
        },
        'unblock': {
            'contact': _('Request to disable enhanced object security of contact %(handle)s'),
            'domain': _('Request to disable enhanced object security of domain name %(handle)s'),
            'nsset': _('Request to disable enhanced object security of nameserver set %(handle)s'),
            'keyset': _('Request to disable enhanced object security of keyset %(handle)s'),
        },
    }


class CustomEmailView(TextPasswordAndBlockMixin, BaseResponseTemplateView):
    """Custom email view."""

    template_name = 'webwhois/public_request_custom_email.html'

    text_subject = {
        'send_password': {
            'contact': _('Subject: Request to send a password (authinfo) for transfer contact %(handle)s:'),
            'domain': _('Subject: Request to send a password (authinfo) for transfer domain name %(handle)s:'),
            'nsset': _('Subject: Request to send a password (authinfo) for transfer nameserver set %(handle)s:'),
            'keyset': _('Subject: Request to send a password (authinfo) for transfer keyset %(handle)s:'),
        },
        'personal_info': _('Request to send personal information of contact %(handle)s:'),
        'block': {
            'contact': _('Subject: Confirmation of the request to enable enhanced object security of '
                         'contact %(handle)s:'),
            'domain': _('Subject: Confirmation of the request to enable enhanced object security of '
                        'domain name %(handle)s:'),
            'nsset': _('Subject: Confirmation of the request to enable enhanced object security of '
                       'nameserver set %(handle)s:'),
            'keyset': _('Subject: Confirmation of the request to enable enhanced object security of '
                        'keyset %(handle)s:'),
        },
        'unblock': {
            'contact': _('Subject: Confirmation of the request to disable enhanced object security of '
                         'contact %(handle)s:'),
            'domain': _('Subject: Confirmation of the request to disable enhanced object security of '
                        'domain name %(handle)s:'),
            'nsset': _('Subject: Confirmation of the request to disable enhanced object security of '
                       'nameserver set %(handle)s:'),
            'keyset': _('Subject: Confirmation of the request to disable enhanced object security of '
                        'keyset %(handle)s:'),
        },
    }
    text_content = {
        'send_password': {
            'contact': _('I hereby confirm my request to get the password for contact %(handle)s, '
                         'submitted through the web form at %(form_url)s on %(created_date)s, assigned id number '
                         '%(response_id)s. Please send the password to %(custom_email)s.'),
            'domain': _('I hereby confirm my request to get the password for domain name %(handle)s, '
                        'submitted through the web form at %(form_url)s on %(created_date)s, assigned id number '
                        '%(response_id)s. Please send the password to %(custom_email)s.'),
            'nsset': _('I hereby confirm my request to get the password for nameserver set %(handle)s, '
                       'submitted through the web form at %(form_url)s on %(created_date)s, assigned id number '
                       '%(response_id)s. Please send the password to %(custom_email)s.'),
            'keyset': _('I hereby confirm my request to get the password for keyset %(handle)s, '
                        'submitted through the web form at %(form_url)s on %(created_date)s, assigned id number '
                        '%(response_id)s. Please send the password to %(custom_email)s.'),
        },
        'personal_info': _('I hereby confirm my request for personal data of the contact %(handle)s, '
                           'submitted through the web form on %(form_url)s on %(created_date)s, assigned the id number '
                           '%(response_id)s. Please send the data to %(custom_email)s.'),
        'block_transfer': {
            'contact': _('I hereby confirm the request to block any change of the sponsoring registrar for the contact '
                         '%(handle)s submitted through the web form on the web site %(form_url)s on %(created_date)s '
                         'with the assigned identification number %(response_id)s, and I request the activation '
                         'of the specified blocking option. I agree that, regarding the particular contact %(handle)s, '
                         'no change of the sponsoring registrar will be possible until I cancel the blocking option '
                         'through the applicable form on %(company_website)s.'),
            'domain': _('I hereby confirm the request to block any change of the sponsoring registrar for the domain '
                        'name %(handle)s submitted through the web form on the web site %(form_url)s on '
                        '%(created_date)s with the assigned identification number %(response_id)s, and I request '
                        'the activation of the specified blocking option. I agree that, regarding the particular '
                        'domain name %(handle)s, no change of the sponsoring registrar will be possible until I cancel '
                        'the blocking option through the applicable form on %(company_website)s.'),
            'nsset': _('I hereby confirm the request to block any change of the sponsoring registrar for '
                       'the nameserver set %(handle)s submitted through the web form on the web site %(form_url)s on '
                       '%(created_date)s with the assigned identification number %(response_id)s, and I request '
                       'the activation of the specified blocking option. I agree that, regarding the particular '
                       'nameserver set %(handle)s, no change of the sponsoring registrar will be possible until '
                       'I cancel the blocking option through the applicable form on %(company_website)s.'),
            'keyset': _('I hereby confirm the request to block any change of the sponsoring registrar for the keyset '
                        '%(handle)s submitted through the web form on the web site %(form_url)s on %(created_date)s '
                        'with the assigned identification number %(response_id)s, and I request the activation '
                        'of the specified blocking option. I agree that, regarding the particular keyset %(handle)s, '
                        'no change of the sponsoring registrar will be possible until I cancel the blocking option '
                        'through the applicable form on %(company_website)s.'),
        },
        'block_all': {
            'contact': _('I hereby confirm the request to block all changes made to contact %(handle)s submitted '
                         'through the web form on the web site %(form_url)s on %(created_date)s with the assigned '
                         'identification number %(response_id)s, and I request the activation of the specified '
                         'blocking option. I agree that, with respect to the particular contact %(handle)s, no change '
                         'will be possible until I cancel the blocking option through the applicable '
                         'form on %(company_website)s.'),
            'domain': _('I hereby confirm the request to block all changes made to domain name %(handle)s submitted '
                        'through the web form on the web site %(form_url)s on %(created_date)s with the assigned '
                        'identification number %(response_id)s, and I request the activation of the specified blocking '
                        'option. I agree that, with respect to the particular domain name %(handle)s, no change '
                        'will be possible until I cancel the blocking option through the applicable '
                        'form on %(company_website)s.'),
            'nsset': _('I hereby confirm the request to block all changes made to nameserver set %(handle)s submitted '
                       'through the web form on the web site %(form_url)s on %(created_date)s with the assigned '
                       'identification number %(response_id)s, and I request the activation of the specified blocking '
                       'option. I agree that, with respect to the particular nameserver set %(handle)s, no change '
                       'will be possible until I cancel the blocking option through the applicable '
                       'form on %(company_website)s.'),
            'keyset': _('I hereby confirm the request to block all changes made to keyset %(handle)s submitted through '
                        'the web form on the web site %(form_url)s on %(created_date)s with the assigned '
                        'identification number %(response_id)s, and I request the activation of the specified blocking '
                        'option. I agree that, with respect to the particular keyset %(handle)s, no change will be '
                        'possible until I cancel the blocking option through the applicable form on '
                        '%(company_website)s.'),
        },
        'unblock_transfer': {
            'contact': _('I hereby confirm the request to cancel the blocking of the sponsoring registrar change '
                         'for the contact %(handle)s submitted through the web form on %(form_url)s on '
                         '%(created_date)s with the assigned identification number %(response_id)s.'),
            'domain': _('I hereby confirm the request to cancel the blocking of the sponsoring registrar change '
                        'for the domain name %(handle)s submitted through the web form on %(form_url)s on '
                        '%(created_date)s with the assigned identification number %(response_id)s.'),
            'nsset': _('I hereby confirm the request to cancel the blocking of the sponsoring registrar change '
                       'for the nameserver set %(handle)s submitted through the web form on %(form_url)s '
                       'on %(created_date)s with the assigned identification number %(response_id)s.'),
            'keyset': _('I hereby confirm the request to cancel the blocking of the sponsoring registrar change '
                        'for the keyset %(handle)s submitted through the web form on %(form_url)s on %(created_date)s '
                        'with the assigned identification number %(response_id)s.'),
        },
        'unblock_all': {
            'contact': _('I hereby confirm the request to cancel the blocking of all changes for the contact '
                         '%(handle)s submitted through the web form on %(form_url)s on %(created_date)s with '
                         'the assigned identification number %(response_id)s.'),
            'domain': _('I hereby confirm the request to cancel the blocking of all changes for the domain name '
                        '%(handle)s submitted through the web form on %(form_url)s on %(created_date)s with '
                        'the assigned identification number %(response_id)s.'),
            'nsset': _('I hereby confirm the request to cancel the blocking of all changes for the nameserver set '
                       '%(handle)s submitted through the web form on %(form_url)s on %(created_date)s with '
                       'the assigned identification number %(response_id)s.'),
            'keyset': _('I hereby confirm the request to cancel the blocking of all changes for the keyset %(handle)s '
                        'submitted through the web form on %(form_url)s on %(created_date)s with the assigned '
                        'identification number %(response_id)s.'),
        },
    }

    def get_context_data(self, **kwargs):
        kwargs.setdefault('company_website', _('the company website'))
        context = super(CustomEmailView, self).get_context_data(**kwargs)
        public_response = self.get_public_response()
        text_context = {'handle': public_response.handle, 'response_id': public_response.public_request_id,
                        'created_date': date_format(public_response.create_date)}
        if isinstance(public_response, SendPasswordResponse):
            text_context['custom_email'] = public_response.custom_email
            text_context['form_url'] = self.request.build_absolute_uri(reverse('webwhois:form_send_password'))

            title = self.text_title['send_password'][public_response.object_type] % text_context
            context['text_title'] = context['text_header'] = title
            context['text_subject'] = self.text_subject['send_password'][public_response.object_type] % text_context
            context['text_content'] = self.text_content['send_password'][public_response.object_type] % text_context
        elif isinstance(public_response, PersonalInfoResponse):
            text_context['custom_email'] = public_response.custom_email
            text_context['form_url'] = self.request.build_absolute_uri(reverse('webwhois:form_personal_info'))

            context['text_title'] = context['text_header'] = self.text_title['personal_info'] % text_context
            context['text_subject'] = self.text_subject['personal_info'] % text_context
            context['text_content'] = self.text_content['personal_info'] % text_context
        else:
            assert isinstance(public_response, BlockResponse)
            if public_response.action == 'block':
                url_name = 'webwhois:form_block_object'
            else:
                url_name = 'webwhois:form_unblock_object'
            text_context['form_url'] = self.request.build_absolute_uri(reverse(url_name))
            text_context['company_website'] = context['company_website']

            action = public_response.action
            title = self.text_title[action][public_response.object_type] % text_context
            context['text_title'] = context['text_header'] = title
            context['text_subject'] = self.text_subject[action][public_response.object_type] % text_context
            key = '%s_%s' % (action, public_response.lock_type)
            context['text_content'] = self.text_content[key][public_response.object_type] % text_context
        return context


class NotarizedLetterView(TextPasswordAndBlockMixin, BaseResponseTemplateView):
    """Notarized letter view."""

    template_name = 'webwhois/public_request_notarized_letter.html'

    def get_context_data(self, **kwargs):
        context = super(NotarizedLetterView, self).get_context_data(**kwargs)
        context['notarized_letter_pdf_url'] = reverse("webwhois:notarized_letter_serve_pdf",
                                                      kwargs={"public_key": kwargs['public_key']},
                                                      current_app=self.request.resolver_match.namespace)

        public_response = self.get_public_response()
        text_context = {'handle': public_response.handle}
        if isinstance(public_response, SendPasswordResponse):
            title = self.text_title['send_password'][public_response.object_type] % text_context
            context['text_title'] = context['text_header'] = title
            context['pdf_name'] = _("Password (authinfo) request")
        elif isinstance(public_response, PersonalInfoResponse):
            title = self.text_title['personal_info'] % text_context
            context['text_title'] = context['text_header'] = title
            context['pdf_name'] = _("Request to personal information")
        else:
            assert isinstance(public_response, BlockResponse)
            if public_response.action == 'block':
                title = self.text_title['block'][public_response.object_type] % text_context
                context['text_title'] = context['text_header'] = title
                context["pdf_name"] = _("Enabling enhanced object security Request")
            else:
                title = self.text_title['unblock'][public_response.object_type] % text_context
                context['text_title'] = context['text_header'] = title
                context["pdf_name"] = _("Disabling enhanced object security Request")
        return context


class ServeNotarizedLetterView(PublicRequestLoggerMixin, View):
    """Serve Notarized letter PDF view."""

    def _get_logging_request_name_and_properties(self, data):
        properties = [
            ("handle", data['handle']),
            ("objectType", data['object_type']),
            ("pdfLangCode", data['lang_code']),
            ("documentType", data['document_type']),
        ]
        if 'custom_email' in data:
            properties.append(('customEmail', data['custom_email']))
        return 'NotarizedLetterPdf', properties

    def get(self, request, public_key):
        public_response = cache.get(public_key)
        if public_response is None:
            raise Http404

        registry_lang_codes = {
            'en': Language.en,
            'cs': Language.cs,
        }
        lang_code = get_language()
        if lang_code not in registry_lang_codes:
            lang_code = 'en'
        language_code = registry_lang_codes[lang_code]

        data = {
            'lang_code': lang_code,
            'document_type': public_response.request_type,
            'handle': public_response.handle,
            'object_type': public_response.object_type,
        }
        if getattr(public_response, 'custom_email', None):
            data['custom_email'] = public_response.custom_email
        if LOGGER:
            log_request = self.prepare_logging_request(data)
            log_request_id = log_request.request_id
        else:
            log_request, log_request_id = None, None
        error_object = None  # type: Optional[BaseException]
        try:
            pdf_content = PUBLIC_REQUEST.create_public_request_pdf(public_response.public_request_id, language_code)
        except OBJECT_NOT_FOUND as err:
            WEBWHOIS_LOGGING.error('Exception OBJECT_NOT_FOUND risen for public request id %s.' % log_request_id)
            error_object = PublicRequestKnownException(type(err).__name__)
            raise Http404
        except BaseException as err:
            error_object = err
            raise
        finally:
            self.finish_logging_request(log_request, public_response.public_request_id, error_object)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="notarized-letter-{0}.pdf"'.format(lang_code)
        response.content = pdf_content

        return response
