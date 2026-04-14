#!/bin/sh
cd /galactic_science_opm
./wait-for-it.sh galactic-science-opm-db:5432 --
python manage.py migrate --noinput

if [ "$LOCAL" = "1" ]; then
    echo "Running local setup"
    ./wait-for-it.sh galactic-science-opm-db-test:5432 --
fi

if [ "$E2E" = "1" ]; then
    echo "Running E2E setup..."
    ./wait-for-it.sh galactic-science-opm-db-test:5432 --
    python manage.py flush --noinput
    python manage.py seed_e2e_data
fi

python manage.py collectstatic --noinput

if [ "$LOCAL" = "1" ]; then
    echo "Running local setup"
    python manage.py runserver 0.0.0.0:8000
else 
    exec gunicorn galactic_science_opm.wsgi \
        -b :80 \
        --access-logfile - \
        --error-logfile - \
        -k gevent  \
        --timeout 10 \
        --graceful-timeout 5 \
        --workers 2 
fi

