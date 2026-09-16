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

show-total-coverage-as-html:
  docker compose exec galactic-science-opm coverage html
  open ./htmlcov/index.html

show-branch-coverage-as-html:
  docker compose exec galactic-science-opm coverage xml
  poetry run diff-cover coverage.xml --format html:report.html --compare-branch=origin/dev
  open ./report.html

show-branch-coverage-as-markdown:
  docker compose exec galactic-science-opm coverage xml
  poetry run diff-cover coverage.xml --format markdown:report.md --compare-branch=origin/dev

exec-django:
  docker compose exec -it galactic-science-opm  /bin/bash
