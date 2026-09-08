start-local:
  docker compose -f compose.base.yaml -f compose.local.yaml up -d

start-local-build:
  docker compose -f compose.base.yaml -f compose.local.yaml up -d --build

log-local:
  docker compose -f compose.base.yaml -f compose.local.yaml logs -f

stop-local:
  docker compose -f compose.base.yaml -f compose.local.yaml down

run-vite:
  cd frontend && npx vite build --watch

start-prod:
  docker compose -f compose.base.yaml -f compose.prod.yaml up -d

start-prod-build:
  docker compose -f compose.base.yaml -f compose.prod.yaml up -d --build

stop-prod:
  docker compose -f compose.base.yaml -f compose.prod.yaml down

run-e2e:
  docker compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml up -d --build

stop-e2e:
  docker compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml down

log-e2e:
  docker compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml logs e2e -f

run-unittest:
  docker compose exec galactic-science-opm  coverage run -m pytest custom_code/tests/unit/

show-html-coverage:
  docker compose exec galactic-science-opm coverage html
  open ./htmlcov/index.html
