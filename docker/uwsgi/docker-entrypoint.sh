#!/bin/sh
set -e

if [ "$1" = "uwsgi" ]; then
    django-admin collectstatic --no-input
fi

exec "$@"
