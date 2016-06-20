import os

from django.conf import settings


def get_dobradomena_list(language):
    """
    Returns dict of dobradomena files for given language.
    """
    if not os.path.isdir(settings.WEBWHOIS_DOBRADOMENA_ROOT):
        return {}

    files = {}
    lang = language.lower()
    for registrar_name in os.listdir(settings.WEBWHOIS_DOBRADOMENA_ROOT):
        if registrar_name == 'www':
            continue  # skip default
        fs_path = os.path.join(settings.WEBWHOIS_DOBRADOMENA_ROOT, registrar_name, lang,
                               settings.WEBWHOIS_DOBRADOMENA_FILE_NAME)
        if os.access(fs_path, os.R_OK):
            files["REG-%s" % registrar_name.upper()] = settings.WEBWHOIS_DOBRADOMENA_MANUAL_URL_PATTERN % {
                "handle": registrar_name, "lang": lang} + settings.WEBWHOIS_DOBRADOMENA_FILE_NAME
    return files
