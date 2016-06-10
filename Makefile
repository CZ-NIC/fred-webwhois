APP = webwhois

.PHONY: default msg msg-py msg-make-py msg-sort-py isort check-isort

default:
	echo "No default action, specify the target"

# Translations
msg: msg-py

msg-py: msg-make-py msg-sort-py

msg-make-py:
	cd ${APP} && django-admin.py makemessages -l cs

msg-sort-py:
	msgattrib --sort-output --no-location --no-obsolete -o ${APP}/locale/cs/LC_MESSAGES/django.po \
		${APP}/locale/cs/LC_MESSAGES/django.po

isort:
	isort --recursive ${APP}

check-isort:
	isort --recursive --check-only --diff ${APP}
