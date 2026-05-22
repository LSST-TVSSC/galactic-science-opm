#!/bin/sh

set -e

echo -n "Waiting for django"

until curl -s -f "$BASE_URL"/health/ > /dev/null; do
    echo -n "."
    sleep 1
done

echo "Django is healthy"