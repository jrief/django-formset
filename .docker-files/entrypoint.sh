#!/bin/bash
set -e
echo "=== Starting django-formset testapp ==="

[[ -z "$DJANGO_WORKDIR" ]] && echo >&2 "Missing environment variable: DJANGO_WORKDIR" && exit 1

if [[ ! -d "$DJANGO_WORKDIR/media" ]] || [[ ! $(ls -A "$DJANGO_WORKDIR/media") ]]; then
	# the directory where Django keeps its media is empty, so set the appropriate permissions
	mkdir --parents "$DJANGO_WORKDIR"
	chown -R django.django "$DJANGO_WORKDIR"
fi

case "X$1" in
	Xuwsgi)
		su django -c "python /web/testapp/manage.py migrate"
		exec "$@" --ini /etc/uwsgi.ini
		;;
	*)
		su django -c "python /web/testapp/manage.py $@"
		;;
esac
