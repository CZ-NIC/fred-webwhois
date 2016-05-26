import os
from urllib import urlencode

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.views.generic import TemplateView, View
from django.views.static import serve

from webwhois.forms import WhoisForm
from webwhois.utils.dobradomena import get_dobradomena_list
from webwhois.views import ContactDetailWithMojeidMixin, DomainDetailMixin, DownloadEvalFileView, KeysetDetailMixin, \
    NssetDetailMixin, RegistrarDetailMixin, RegistrarListMixin, ResolveHandleTypeMixin, WhoisFormView
from webwhois.views.pages import FILEMANAGER, WHOIS

from .constants import URLS_NAMESPACE


class WhoisWithCaptchaForm(WhoisForm):
    captcha = ReCaptchaField()


class SiteMenuMixin(object):

    base_template = "base_site.html"

    def get_context_data(self, **kwargs):
        kwargs.setdefault("base_template", self.base_template)
        kwargs.setdefault("page_url_name", (":".join((self.request.resolver_match.namespace, self.request.resolver_match.url_name))).lstrip(":"))
        kwargs.setdefault("standalone", {
            "home_page": "home_page",
            "form_whois": "%s:form_whois" % URLS_NAMESPACE,
            "registrar_list_retail": "%s:registrar_list_retail" % URLS_NAMESPACE,
            "registrar_list_wholesale": "%s:registrar_list_wholesale" % URLS_NAMESPACE,
            "form_public_request": "%s:form_public_request" % URLS_NAMESPACE,
            "registry_object_type": "%s:registry_object_type" % URLS_NAMESPACE,
            "detail_contact": "%s:detail_contact" % URLS_NAMESPACE,
            "detail_nsset": "%s:detail_nsset" % URLS_NAMESPACE,
            "detail_keyset": "%s:detail_keyset" % URLS_NAMESPACE,
            "detail_domain": "%s:detail_domain" % URLS_NAMESPACE,
            "detail_registrar": "%s:detail_registrar" % URLS_NAMESPACE,
        })
        return super(SiteMenuMixin, self).get_context_data(**kwargs)


get_captcha_cache_key = lambda request: 'webwhois_captcha_limit:%s' % request.META.get('REMOTE_ADDR')


class CountCaptchaMixin(SiteMenuMixin):

    _WHOIS = WHOIS
    redirect_to_form = '%s:form_whois' % URLS_NAMESPACE

    def dispatch(self, request, *args, **kwargs):
        cache_key = get_captcha_cache_key(request)
        used_n_times = cache.get(cache_key, 0) + 1
        cache.set(cache_key, used_n_times)
        if used_n_times > settings.WEBWHOIS_CAPTCHA_MAX_REQUESTS:
            return redirect(reverse(self.redirect_to_form) + "?" + urlencode({"handle": kwargs.get("handle")}))
        return super(CountCaptchaMixin, self).dispatch(request, *args, **kwargs)


class HomePageView(SiteMenuMixin, TemplateView):
    template_name = "webwhois_standalone/home_page.html"


class WebwhoisFormView(SiteMenuMixin, WhoisFormView):

    _WHOIS = WHOIS
    template_name = "webwhois_in_cms/form_whois.html"
    captcha_limit = 'webwhois_captcha_limit:%s'

    def get_context_data(self, **kwargs):
        kwargs.setdefault("WHOIS_SEARCH_ENGINES", settings.WEBWHOIS_SEARCH_ENGINES)
        kwargs.setdefault("managed_zone_list", self._WHOIS.get_managed_zone_list())
        return super(WebwhoisFormView, self).get_context_data(**kwargs)

    def get_form_class(self):
        if cache.get(get_captcha_cache_key(self.request), 0) >= settings.WEBWHOIS_CAPTCHA_MAX_REQUESTS:
            return WhoisWithCaptchaForm
        return self.form_class

    def form_valid(self, form):
        if isinstance(form, WhoisWithCaptchaForm):
            cache.delete(get_captcha_cache_key(self.request))
        return super(WebwhoisFormView, self).form_valid(form)

    def form_invalid(self, form):
        key = get_captcha_cache_key(self.request)
        cache.set(key, cache.get(key, 0) + 1)
        if isinstance(form, WhoisWithCaptchaForm) and not form.errors.get('captcha'):
            cache.delete(key)
        return super(WebwhoisFormView, self).form_invalid(form)


class WebwhoisResolveHandleTypeView(CountCaptchaMixin, ResolveHandleTypeMixin, TemplateView):
    pass


class WebwhoisContactDetailView(CountCaptchaMixin, ContactDetailWithMojeidMixin, TemplateView):
    pass


class WebwhoisNssetDetailView(CountCaptchaMixin, NssetDetailMixin, TemplateView):
    pass


class WebwhoisKeysetDetailView(CountCaptchaMixin, KeysetDetailMixin, TemplateView):
    pass


class WebwhoisDomainDetailView(CountCaptchaMixin, DomainDetailMixin, TemplateView):
    pass


class WebwhoisRegistrarDetailView(SiteMenuMixin, RegistrarDetailMixin, TemplateView):
    _WHOIS = WHOIS


class WebwhoisRegistrarListView(SiteMenuMixin, RegistrarListMixin, TemplateView):
    template_name = "webwhois_in_cms/registrar_list_with_dobradomena.html"
    _WHOIS = WHOIS

    def _registrar_row(self, data):
        # self._dobradomena_dict: {'REG-NIC': 'http://nic.dobradomena.cz/dobradomena/manual.pdf', ...}
        data["dobradomena"] = self._dobradomena_dict.get(data['registrar'].handle)
        return data

    def get_context_data(self, **kwargs):
        kwargs.setdefault("HOW_TO_BECOME_A_REGISTRAR_URL", settings.WEBWHOIS_HOW_TO_BECOME_A_REGISTRAR_URL)
        kwargs.setdefault("REGISTRAR_CERTIFIED_FOR_RETAIL_URL", settings.WEBWHOIS_REGISTRAR_CERTIFIED_FOR_RETAIL_URL)
        self._dobradomena_dict = get_dobradomena_list(get_language())
        return super(WebwhoisRegistrarListView, self).get_context_data(**kwargs)


class WebwhoisDownloadEvalFileView(DownloadEvalFileView):
    _WHOIS = WHOIS
    _FILE = FILEMANAGER


class DobradomenaServeFile(View):

    def get(self, request, handle, lang):
        path = os.path.join(handle, lang, settings.WEBWHOIS_DOBRADOMENA_FILE_NAME)
        return serve(self.request, path, document_root=settings.WEBWHOIS_DOBRADOMENA_ROOT)


class PublicRequestView(SiteMenuMixin, TemplateView):
    template_name = "webwhois_standalone/webwhois_public_request.html"
