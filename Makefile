APP = webwhois

.PHONY: default msg msg-py msg-make-py msg-sort-py test isort check-isort check-flake8

default:
	echo "No default action, specify the target"

# Translations
msg: msg-py

msg-py: msg-make-py msg-sort-py

msg-make-py:
	cd ${APP} && django-admin makemessages -l cs

msg-sort-py:
	msgattrib --sort-output --no-location --no-obsolete -o ${APP}/locale/cs/LC_MESSAGES/django.po \
		${APP}/locale/cs/LC_MESSAGES/django.po

test:
	PYTHONPATH='./test_cfg:${PYTHONPATH}' DJANGO_SETTINGS_MODULE='settings' django-admin test webwhois

isort:
	isort --recursive ${APP}

check-isort:
	isort --recursive --check-only --diff ${APP}

check-flake8:
	flake8 --config=.flake8 --format=pylint --show-source ${APP}
