#!/bin/sh
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
gunicorn Extractor.wsgi:application --workers 3 --threads 4 --preload --bind 0.0.0.0:8000
