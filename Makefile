APP = webwhois
TRANSLATIONS = ${APP}/locale/cs/LC_MESSAGES/django.po

.PHONY: default msg msg-py msg-make-py msg-sort-py test isort check-isort check-flake8 check-i18n check-doc check-all

default: check-all

# Translations
msg: msg-py

msg-py: msg-make-py msg-sort-py

msg-make-py:
	cd ${APP} && django-admin makemessages -l cs

msg-sort-py:
	msgattrib --sort-output --no-location --no-obsolete -o ${TRANSLATIONS} ${TRANSLATIONS}

test:
	PYTHONPATH='./test_cfg:${PYTHONPATH}' DJANGO_SETTINGS_MODULE='settings' django-admin test webwhois

test-coverage:
	PYTHONPATH='./test_cfg:${PYTHONPATH}' DJANGO_SETTINGS_MODULE='settings' coverage run --source=${APP} --branch -m django test ${APP}

isort:
	isort --recursive ${APP}

check-all: check-isort check-flake8 check-i18n check-doc

check-isort:
	isort --recursive --check-only --diff ${APP}

check-flake8:
	flake8 --config=.flake8 --format=pylint --show-source ${APP}

check-doc:
	pydocstyle ${APP}

check-i18n:
	# Ensure catalog is complete - make C locales to generate POT files and compare it using the msgcmp
	cd ${APP} && django-admin makemessages --locale C --no-obsolete --no-location --keep-pot
	msgcmp ${TRANSLATIONS} ${APP}/locale/django.pot
	-rm -r ${APP}/locale/django.pot ${APP}/locale/C
