#!/usr/bin/env bash
cd /galactic_science_opm
poetry run ./manage.py migrate --noinput
poetry run ./manage.py collectstatic --noinput
poetry run gunicorn -b :80 galactic_science_opm.wsgi --access-logfile - --error-logfile - -k gevent  --timeout 300 --workers 2
