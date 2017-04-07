import os

from django.core.exceptions import ImproperlyConfigured

from webwhois.settings import WEBWHOIS_DOBRADOMENA_FILE_NAME, WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN, \
    WEBWHOIS_DOBRADOMENA_ROOT


def get_dobradomena_list(language):
    """
    Returns dict of dobradomena files for given language.
    """
    if not WEBWHOIS_DOBRADOMENA_ROOT or not os.path.isdir(WEBWHOIS_DOBRADOMENA_ROOT):
        return {}

    if not WEBWHOIS_DOBRADOMENA_FILE_NAME:
        raise ImproperlyConfigured(
            "WEBWHOIS_DOBRADOMENA_ROOT is set but WEBWHOIS_DOBRADOMENA_FILE_NAME missing.")
    if not WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN:
        raise ImproperlyConfigured(
            "WEBWHOIS_DOBRADOMENA_ROOT is set but WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN missing.")

    files = {}
    lang = language.lower()
    for registrar_name in os.listdir(WEBWHOIS_DOBRADOMENA_ROOT):
        if registrar_name == 'www':
            continue  # skip default
        fs_path = os.path.join(WEBWHOIS_DOBRADOMENA_ROOT, registrar_name, lang, WEBWHOIS_DOBRADOMENA_FILE_NAME)
        if os.access(fs_path, os.R_OK):
            files["REG-%s" % registrar_name.upper()] = WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN % {
                "handle": registrar_name, "lang": lang} + WEBWHOIS_DOBRADOMENA_FILE_NAME
    return files
