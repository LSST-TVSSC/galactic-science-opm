#!/bin/sh
start=$(date +%s)

docker-compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml up -d --force-recreate galactic-science-opm galactic-science-opm-db-test frontend-proxy
#docker exec galactic-science-opm-galactic-science-opm-1 sh -c "./wait-for-it.sh galactic-science-opm-db:5432 --timeout=10 --strict --"
docker exec galactic-science-opm-galactic-science-opm-1 sh -c "./wait-for-healthy.sh"
docker-compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml run --rm e2e
docker exec galactic-science-opm-galactic-science-opm-1 sh -c "python manage.py flush --noinput"
docker-compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml down
end=$(date +%s)
duration=$((end - start)) 

echo "E2E tests took $duration s"
