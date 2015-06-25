import os
import sys

from captcha.fields import ReCaptchaField
from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.utils.functional import SimpleLazyObject
from django.views.generic import FormView, TemplateView, View
from omniORB import CORBA, importIDL

from webwhois.utils.corba import Corba
from webwhois.utils.corbarecoder import c2u, u2c


if hasattr(settings, 'CORBA_MOCK') and settings.CORBA_MOCK:
    from webwhois.utils.corba_mock import WhoisIntfMock, FileManagerMock
    _WHOIS = WhoisIntfMock()
    _FILE = FileManagerMock()
else:
    importIDL('%s/%s' % (settings.CORBA_IDL_ROOT_PATH, settings.CORBA_IDL_FILEMANAGER_FILENAME))
    importIDL('%s/%s' % (settings.CORBA_IDL_ROOT_PATH, settings.CORBA_IDL_WHOIS_FILENAME))
    _CORBA = Corba(ior=settings.CORBA_NS_HOST_PORT, context_name=settings.CORBA_NS_CONTEXT,
                   export_modules=settings.CORBA_EXPORT_MODULES)
    _WHOIS = SimpleLazyObject(lambda: _CORBA.get_object('Whois2', 'Registry.Whois.WhoisIntf'))
    _FILE = SimpleLazyObject(lambda: _CORBA.get_object('FileManager', 'ccReg.FileManager'))


Registry = sys.modules['Registry']


handle_types = {
    'registrar': _WHOIS.get_registrar_by_handle,
    'contact': _WHOIS.get_contact_by_handle,
    'nsset': _WHOIS.get_nsset_by_handle,
    'keyset': _WHOIS.get_keyset_by_handle,
    'domain': _WHOIS.get_domain_by_handle,
}


def load_handle(handle, handle_type):
    """
    Loads given handle with given handle_type from Corba
    """
    if handle_type not in handle_types:
        return None
    cache_key = 'webwhois_loaded_handles_%s:%s' % (handle_type, handle.upper())
    cached_handle = cache.get(cache_key)
    if cached_handle is None:
        fn = handle_types[handle_type]
        try:
            loaded_handle = c2u(fn(u2c(handle)))
            cache.set(cache_key, loaded_handle)
            return loaded_handle
        except CORBA.UserException as e:
            cache.set(cache_key, e)
            raise e
    elif isinstance(cached_handle, Exception):
        raise cached_handle
    else:
        return cached_handle

status_types = {
    'contact': _WHOIS.get_contact_status_descriptions,
    'nsset': _WHOIS.get_nsset_status_descriptions,
    'keyset': _WHOIS.get_keyset_status_descriptions,
    'domain': _WHOIS.get_domain_status_descriptions,
}


def get_status_desc(status, status_type, lang):
    """
    Loads status description of status identification of given status_type from Corba
    """
    if status_type not in status_types:
        return None
    cache_key = 'webwhois_loaded_statuses_%s:%s' % (lang, status_type)
    statuses = cache.get(cache_key)
    if statuses is None:
        fn = status_types[status_type]
        statuses = {}
        try:
            res = c2u(fn(u2c(lang)))
            for st in res:
                statuses[st.handle] = st.name
            cache.set(cache_key, statuses)
        except:
            pass

    return statuses.get(status)


def get_captcha_cache_key(request):
    """
    Returns key for cache based on IP address of request for captcha
    """
    ip = request.META.get('REMOTE_ADDR')
    return 'webwhois_captcha_limit:%s' % ip


def get_dobradomena_list(language):
    """
    Returns dict of dobradomena files for given language
    """
    dobradomena = {}

    files_root = settings.DOBRADOMENA_DIR
    docname = settings.DOBRADOMENA_FILE_NAME
    hostname = settings.DOBRADOMENA_HOST

    for registrar_name in os.listdir(files_root):
        if registrar_name == 'www':
            continue  # skip default

        fs_path = os.path.join(files_root, registrar_name, language.lower(), docname)
        if os.access(fs_path, os.R_OK):
            link = "http://%s.%s/dobradomena/%s" % (registrar_name, hostname, docname)
            dobradomena["REG-%s" % registrar_name.upper()] = link

    return dobradomena


CONTACT_STATUS_VERIF = ['conditionallyIdentifiedContact', 'identifiedContact',
                        'validatedContact', 'contactPassedManualVerification',
                        'contactInManualVerification', 'contactFailedManualVerification']


class QueryForm(forms.Form):

    handle = forms.CharField(widget=forms.TextInput(attrs={'class': 'inline'}))

    def __init__(self, *args, **kwargs):
        super(QueryForm, self).__init__(*args, **kwargs)
        self.available_entities = {}

    def is_valid(self):
        if not super(QueryForm, self).is_valid():
            return False
        else:
            for handle_type in ('registrar', 'contact', 'nsset', 'keyset', 'domain'):
                try:
                    loaded_handle = load_handle(self.cleaned_data['handle'], handle_type)
                    if loaded_handle:
                        self.available_entities[handle_type] = loaded_handle
                except:
                    pass

            return len(self.available_entities) == 1


class QueryCaptchaForm(QueryForm):

    captcha = ReCaptchaField(attrs={'theme': 'clean'})


class WhoisQueryView(FormView):

    template_name = 'query.html'
    form_class = QueryForm
    success_url = None

    def get_context_data(self, **kwargs):
        context = super(WhoisQueryView, self).get_context_data(**kwargs)
        if self.default_context_function:
            parent_context = self.default_context_function(self.request)
            parent_context.update(context)
            return parent_context
        return context

    def dispatch(self, request, *args, **kwargs):
        cache_key = get_captcha_cache_key(request)
        if cache.get(cache_key, 0) >= settings.CAPTCHA_MAX_REQUESTS:
            self.form_class = QueryCaptchaForm
        self.default_context_function = kwargs.get('default_context_function')
        return super(WhoisQueryView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super(WhoisQueryView, self).get_initial()
        initial["handle"] = self.kwargs.get("handle")
        return initial

    def form_valid(self, form):
        entity_type, entity = form.available_entities.iteritems().next()
        self.success_url = reverse(entity_type, args=(entity.handle,))
        if isinstance(form, QueryCaptchaForm):
            cache_key = get_captcha_cache_key(self.request)
            cache.delete(cache_key)
        return super(WhoisQueryView, self).form_valid(form)

    def form_invalid(self, form):
        if isinstance(form, QueryCaptchaForm) and not form.errors.get('captcha'):
            cache_key = get_captcha_cache_key(self.request)
            cache.delete(cache_key)
        if len(form.available_entities) == 0 and not form.errors.get('captcha') and 'handle' in form.cleaned_data:
            return redirect('domain', form.cleaned_data['handle'])
        return super(WhoisQueryView, self).form_invalid(form)


class DetailMixinView(TemplateView):

    def dispatch(self, request, *args, **kwargs):
        cache_key = get_captcha_cache_key(request)
        if cache.get(cache_key, 0) > settings.CAPTCHA_MAX_REQUESTS:
            return redirect('captcha', kwargs.get('handle'))
        cache.add(cache_key, 0)
        cache.incr(cache_key)
        return super(DetailMixinView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DetailMixinView, self).get_context_data(**kwargs)
        if 'default_context_function' in kwargs:
            parent_context = kwargs['default_context_function'](self.request)
            parent_context.update(context)
            return parent_context
        return context

    def make_address_string(self, address):
        return ', '.join([x for x in [address.street1, address.street2, address.street3, address.postalcode,
                                      address.city, address.stateorprovince, address.country_code] if x])

    def make_statuses_desc(self, statuses, status_type, lang):
        ret = []
        for status in statuses:
            desc = get_status_desc(status, status_type, lang)
            if desc:
                ret.append(desc)
        return ret

    def deep_load_domain(self, handle):
        data = load_handle(handle, 'domain')
        data.registrant = load_handle(data.registrant_handle, 'contact')
        data.admins = []
        for admin in data.admin_contact_handles:
            data.admins.append(load_handle(admin, 'contact'))
        data.registrar = load_handle(data.registrar_handle, 'registrar')
        data.nsset = self.deep_load_nsset(data.nsset_handle) if data.nsset_handle else None
        data.keyset = self.deep_load_keyset(data.keyset_handle) if data.keyset_handle else None
        data.statuses_desc = self.make_statuses_desc(data.statuses, 'domain', get_language())
        return data

    def deep_load_nsset(self, handle):
        data = load_handle(handle, 'nsset')
        data.admins = []
        for admin in data.tech_contact_handles:
            data.admins.append(load_handle(admin, 'contact'))
        data.registrar = load_handle(data.registrar_handle, 'registrar')
        data.statuses_desc = self.make_statuses_desc(data.statuses, 'nsset', get_language())
        return data

    def deep_load_keyset(self, handle):
        data = load_handle(handle, 'keyset')
        data.admins = []
        for admin in data.tech_contact_handles:
            data.admins.append(load_handle(admin, 'contact'))
        data.registrar = load_handle(data.registrar_handle, 'registrar')
        data.statuses_desc = self.make_statuses_desc(data.statuses, 'keyset', get_language())
        return data

    def deep_load_contact(self, handle):
        data = load_handle(handle, 'contact')
        data.moje_id = 'mojeidContact' in data.statuses

        data.statuses_verif = [(st, get_status_desc(st, 'contact', get_language()))
                               for st in data.statuses if st in CONTACT_STATUS_VERIF]

        data.creating_registrar = load_handle(data.creating_registrar_handle, 'registrar')
        data.sponsoring_registrar = load_handle(data.sponsoring_registrar_handle, 'registrar')
        data.address_string = self.make_address_string(data.address.value)

        statuses_base = [st for st in data.statuses if st not in CONTACT_STATUS_VERIF]
        data.statuses_desc = self.make_statuses_desc(statuses_base, 'contact', get_language())

        return data

    def deep_load_registrar(self, handle):
        data = load_handle(handle, 'registrar')
        data.address_string = self.make_address_string(data.address)
        return data


class DomainDetailView(DetailMixinView):

    template_name = "domain.html"

    def get_context_data(self, handle, **kwargs):
        context = super(DomainDetailView, self).get_context_data(**kwargs)
        context['handle'] = handle
        try:
            data = self.deep_load_domain(handle)
            context['data'] = data
        except Registry.Whois.OBJECT_NOT_FOUND:
            context['error'] = 'not_found'
        except Registry.Whois.INVALID_LABEL:
            context['error'] = 'invalid_label'
        except Registry.Whois.TOO_MANY_LABELS:
            context['error'] = 'too_many_labels'
        except Registry.Whois.UNMANAGED_ZONE:
            context['error'] = 'unmanaged_zone'
        return context


class ContactDetailView(DetailMixinView):

    template_name = "contact.html"

    def get_context_data(self, handle, **kwargs):
        context = super(ContactDetailView, self).get_context_data(**kwargs)
        context['handle'] = handle
        context['mojeid_registry_endpoint'] = settings.MOJEID_REGISTRY_ENDPOINT
        context['mojeid_transfer_endpoint'] = settings.MOJEID_TRANSFER_ENDPOINT
        try:
            data = self.deep_load_contact(handle)
            context['data'] = data
        except Registry.Whois.OBJECT_NOT_FOUND:
            context['error'] = 'not_found'
        except Registry.Whois.INVALID_HANDLE:
            context['error'] = 'invalid_handle'
        return context


class NssetDetailView(DetailMixinView):

    template_name = "nsset.html"

    def get_context_data(self, handle, **kwargs):
        context = super(NssetDetailView, self).get_context_data(**kwargs)
        context['handle'] = handle
        try:
            data = self.deep_load_nsset(handle)
            context['data'] = data
        except Registry.Whois.OBJECT_NOT_FOUND:
            context['error'] = 'not_found'
        except Registry.Whois.INVALID_HANDLE:
            context['error'] = 'invalid_handle'
        return context


class KeysetDetailView(DetailMixinView):

    template_name = "keyset.html"

    def get_context_data(self, handle, **kwargs):
        context = super(KeysetDetailView, self).get_context_data(**kwargs)
        context['handle'] = handle
        try:
            data = self.deep_load_keyset(handle)
            context['data'] = data
        except Registry.Whois.OBJECT_NOT_FOUND:
            context['error'] = 'not_found'
        except Registry.Whois.INVALID_HANDLE:
            context['error'] = 'invalid_handle'
        return context


class RegistrarDetailView(DetailMixinView):

    template_name = "registrar.html"

    def get_context_data(self, handle, **kwargs):
        context = super(RegistrarDetailView, self).get_context_data(**kwargs)
        context['handle'] = handle
        try:
            data = self.deep_load_registrar(handle)
            context['data'] = data
        except Registry.Whois.OBJECT_NOT_FOUND:
            context['error'] = 'not_found'
        except Registry.Whois.INVALID_HANDLE:
            context['error'] = 'invalid_handle'
        return context


class RegistrarsListView(TemplateView):

    template_name = "registrars.html"

    def get_context_data(self, **kwargs):
        context = super(RegistrarsListView, self).get_context_data(**kwargs)
        if 'default_context_function' in kwargs:
            parent_context = kwargs['default_context_function'](self.request)
            parent_context.update(context)
            context = parent_context

        is_retail = kwargs.get("retail")

        group_list = c2u(_WHOIS.get_registrar_groups())
        groups = {u"certified": [], u"dnssec": [], u"ipv6": [], u"mojeid": [], u"uncertified": []}
        for group in group_list:
            if group.name in groups:
                groups[group.name] = group.members

        cert_list = c2u(_WHOIS.get_registrar_certification_list())
        certs = {}
        for cert in cert_list:
            certs[cert.registrar_handle] = cert

        data = c2u(_WHOIS.get_registrars())
        for reg in data[:]:
            if (is_retail and reg.handle not in groups[u"certified"]) or \
                    ((not is_retail) and reg.handle not in groups[u"uncertified"]):
                data.remove(reg)
            else:
                if reg.handle in certs:
                    reg.score = certs[reg.handle].score
                    reg.evaluation_file_id = certs[reg.handle].evaluation_file_id
                else:
                    reg.score = 0
                    reg.evaluation_file_id = 0
        context['groups'] = groups
        context['data'] = data
        context['dobradomena'] = get_dobradomena_list(get_language())
        context['retail'] = is_retail

        return context


class DownloadEvalFileView(View):

    def _get_file_response(self, file_id):
        try:
            file_info = c2u(_FILE.info(long(file_id)))
            file_download = _FILE.load(file_info.id)
            file_data = file_download.download(file_info.size)
            file_download.finalize_download()
        except:
            raise Http404

        response = HttpResponse(mimetype=file_info.mimetype)
        response['Content-Disposition'] = 'attachment; filename="%s"' % file_info.name
        response.write(file_data)
        return response

    def get(self, request, handle, **kwargs):
        cert_list = c2u(_WHOIS.get_registrar_certification_list())
        for cert in cert_list:
            if cert.registrar_handle == handle:
                return self._get_file_response(cert.evaluation_file_id)
        raise Http404
