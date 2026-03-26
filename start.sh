#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py process_import_jobs --sleep 3 &
exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 2 --threads 4
