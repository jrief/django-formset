#!/bin/bash
set -e
echo "=== Starting django-formset testapp ==="

[[ -z "$DJANGO_WORKDIR" ]] && echo >&2 "Missing environment variable: DJANGO_WORKDIR" && exit 1
mkdir --parents "$DJANGO_WORKDIR"
chown -R django.django "$DJANGO_WORKDIR"

export PYTHONPATH="/web"

case "X$1" in
	Xuwsgi)
		su django -c "python /web/testapp/manage.py migrate"
		exec "$@" --ini /etc/uwsgi.ini
		;;
	*)
		su django -c "python /web/testapp/manage.py $@"
		;;
esac
