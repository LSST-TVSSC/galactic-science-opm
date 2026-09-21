# FRONTEND BUILD
FROM node:22-alpine AS frontend
LABEL maintainer="llindstrom@lco.global"
LABEL maintainer="markus.hundertmark@uni-heidelberg.de"
LABEL maintainer="max.kistner@uni-heidelberg.de"

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend .
RUN npm run build

# Django build
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /galactic_science_opm

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip && \
    # mkistner: This had to be pinned, because builds were failing on my machine
    # starting 2026-09-21, see the following link where the changes were made
    # which introduced the bug:
    # https://github.com/pypa/virtualenv/commit/fc2f35f51d563c495564f4709ec1a22f0c686352
    # see file src/virtualenv/activation/cshell/__init__.py: deactivate.csh 
    # was not there before and now it is. The error I saw referenced this 
    # file and said it was missing. Pinning should keep this from happening.
    # But this should be looked into again from time to time.
    pip install "virtualenv==21.7.14" && \
    pip install "poetry >=2.0,<3.0"

COPY pyproject.toml poetry.lock /galactic_science_opm/

# tell poetry: do NOT create a virtual env; should install everything globally
# tell poetry: even if you find a virtual env, don't use it; install everything globally
# now have poetry install dependencies according to pyproject.toml
RUN poetry config virtualenvs.create false --local && \
    poetry config virtualenvs.in-project false --local && \
    poetry install --no-interaction --no-root

COPY . .

# copy vite assets
COPY --from=frontend /custom_code/static/custom_code/dist ./static/custom_code/dist

RUN chmod +x /galactic_science_opm/entrypoint.sh
RUN chmod +x /galactic_science_opm/wait-for-healthy.sh
CMD ["/galactic_science_opm/entrypoint.sh"]
