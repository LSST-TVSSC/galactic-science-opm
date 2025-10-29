FROM python:3.11
LABEL maintainer="llindstrom@lco.global"
LABEL maintainer="markus.hundertmark@uni-heidelberg.de"

# the exposed port must match the deployment.yaml containerPort value
EXPOSE 80
ENTRYPOINT [ "poetry", "run", "gunicorn", "galactic_science_opm.wsgi", "-b", "0.0.0.0:80", "--access-logfile", "-", "--error-logfile", "-", "-k", "gevent", "--timeout", "300", "--workers", "2"]

WORKDIR /galactic_science_opm

RUN pip install --upgrade pip && pip install 'poetry >=2.0,<3.0'

COPY . /galactic_science_opm

# tell poetry: do NOT create a virtual env; should install everything globally
RUN poetry config virtualenvs.create false --local
# tell poetry: even if you find a virtual env, don't use it; install everything globally
RUN poetry config virtualenvs.in-project false --local
# now have poetry install dependencies according to pyproject.toml
RUN poetry install -vv --no-interaction

RUN poetry run python manage.py collectstatic --noinput
