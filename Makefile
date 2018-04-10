APP = webwhois
TRANSLATIONS = ${APP}/locale/cs/LC_MESSAGES/django.po

.PHONY: default msg msg-py msg-make-py msg-sort-py test isort

default: test

# Translations
msg: msg-py

msg-py: msg-make-py msg-sort-py

msg-make-py:
	unset -v DJANGO_SETTINGS_MODULE; cd ${APP} && django-admin makemessages -l cs

msg-sort-py:
	msgattrib --sort-output --no-location --no-obsolete -o ${TRANSLATIONS} ${TRANSLATIONS}

test:
	tox

isort:
	isort --recursive ${APP}
