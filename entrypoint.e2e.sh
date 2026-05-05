#!/usr/bin/env bash
cd /code
echo "Preparing e2e tests..."
./wait-for-it.sh galactic-science-opm-db-test:5432 --
./wait-for-healthy.sh
echo "Starting E2E tests."
pytest custom_code/tests/e2e -rs
