# Observation Priority Manager (OPM)

The Observation Priority Manager (OPM) for Galactic Science in the TVSSC.

## Observational Planning/Priority Manager (OPM) - A Target and Observation Manager Instance for the TVS galactic science community

The OPM is an instance of the Target and Observation Manager
([TOM Toolkit](https://tom-toolkit.readthedocs.io/en/stable/)) designed to track
galactic science alerts over time, ingest targets with their alert priority,
display corresponding light curves, and communicate with other TOM systems
connected to observatories and proposals. This repository provides a system that
can be installed locally by members of the TVS galactic science community, for
instance the Microlensing Subgroup, and eventually deployed in a suitable cloud
environment.

## Usage

Once installed, you can access and interact with the OPM through its web
interface. Here are some key features of the system:

- **Target Management**: Create, view, and update targets associated with
  microlensing alerts, subscribe to broker services
- **Light Curve Visualization**: View and analyze light curves associated with
  each target to monitor microlensing events over time.

## Planned Features

- **Communication with Other TOM Systems**: Interact with other TOM systems
  connected to observatories and proposals, enabling easy requesting of
  observations directly from the OPM interface.
- **Requesting and interacting with HPC systems to fit events**: Interact safely
  with HPC centers to fit complicated microlensing events, i.e. binary and
  triple lens events

## Quick start (local docker-based dev setup)

### Requirements

- `docker` or other compatible solution such as `podman`
- `nodejs` and `npm`
  - best installed using
    [nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Steps

1. Clone the repository and change your directory in to the cloned repo.

2. Start the docker containers using the following command:

```bash
docker compose -f compose.base.yaml -f compose.local.yaml up -d
# or the following, if there have been significant changes or it has been a while
docker compose -f compose.base.yaml -f compose.local.yaml up -d --build
```

This will, according to the `compose.*.yaml` files, build a docker image, run it
in a container, using a Postgresql database running in another container.

3. Change into the directory `frontend` and run:

```sh
npm install
npx vite build
```

This builds the frontend assets.

4. Point your browser to http://127.0.0.1:8000 for the Galactic Science OPM home
   page running locally.

5. When the database is empty, you may want to create an admin user for your
   TOM. You can do so by running the Django `createsuperuser` management command
   in the the container. First 'exec' into the container:

```bash
docker exec -it galactic-science-opm-galactic-science-opm-1 /bin/bash
```

In the container's bash shell (that you just opened):

```bash
./manage.py createsuperuser
```

Ctrl-d to leave the container. Log into the OPM with the credentials you just
created.

To stop the containers:

```bash
docker compose -f compose.base.yaml -f compose.local.yaml down
```

## Setting up for local development without docker

### Requirements

- a compatible version of Python
- the package manager
  [poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
- `nodejs` and `npm`
  - best installed using
    [nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Steps

After cloning the repository and changing your directory (`cd`-ing) into the
cloned repo:

#### 1. Create a virtual environment

Always work in a virtual environment. To create and activate one:

```bash
python -m venv .venv
source .venv/bin/activate
```

#### 2. Install the dependencies

There are more than one way to do this. The `pyproject.toml` project description
file is common to all of them. Here, we use `poetry`:

```bash
poetry install
```

#### 3. Work in a branch for the development that you'll be doing

If you've just cloned the repo, you'll be in the `dev` branch. You'll want to do
your development in a branch that can later be merged into the `dev` branch (and
ultimately into the `main` branch for deployment). With the `-b` switch,
`git checkout` creates a new branch.If the branch you want already exists, you
don't need the `-b` switch.

```bash
git checkout -b <name-of-your-branch>
```

#### 4. Spin up a database for your development OPM to use

We quote from
[settings.py](https://github.com/LSST-TVSSC/galactic-science-opm/blob/c0d47f68bd4ed2d8721ef3b0cf900eb5ae75a81e/galactic_science_opm/settings.py#L113):

```python
# Here is how to start a dockerized postgresql container compatible with the default
# values in the 'default' DATABASEs configuration below:

# 1. create a postgres docker image named 'opm-tom-postgres':
# docker create --name opm-tom-postgres -e POSTGRES_DB=galactic_science_opm -e POSTGRES_PASSWORD=opm -e POSTGRES_USER=opm -p 5432:5432 postgres

# 2. start the container from that image
# docker start opm-tom-postgres

# 3.(optional -- this is for completeness) If you want to shut down the dockerized postgres server started in step 2:
# docker stop  opm-tom-postgres

# Also, NOTE: the values in the configuration dictionary below are also referenced in the compose.yaml file!!
```

#### 5. Build the frontend assets

Change into the directory `frontend` and run:

```sh
npm install
npx vite build
```

This builds the frontend assets.

#### 6. Start the Django development server

```bash
./manage.py runserver
```

Point your browser to http://127.0.0.1:8000 for the Galactic Science OPM home
page running locally.

## Additional info for starting up

### Local setup

Uses django dev server for faster iterations.

```sh
docker compose -f compose.base.yaml -f compose.local.yaml up -d
docker compose -f compose.base.yaml -f compose.local.yaml down
```

### Prod like setup

```sh
docker compose -f compose.base.yaml -f compose.prod.yaml up -d
docker compose -f compose.base.yaml -f compose.prod.yaml down
```

### E2E debugging setup

This can be used to make debugging easier when writing end to end tests. It does
not run with the actual e2e setup (which would use nginx) but with Django's dev
server.

```sh
docker compose -f compose.base.yaml -f compose.local.yaml -f compose.e2e.yaml up -d
docker compose -f compose.base.yaml -f compose.local.yaml -f compose.e2e.yaml down
```

Note that this will not automatically run the e2e tests without overriding the
`BASE_URL`, because it wants to run against the frontend-proxy as defined in
`compose.e2e.yaml` but it does not exist here. If you want to run the tests
immediately, use this:

```sh
BASE_URL="http://galactic-science-opm:8000" \
docker-compose -f compose.base.yaml -f compose.local.yaml -f compose.e2e.yaml up -d
```

## Notes on testing

### Running unit tests

Can also be run in your local directory, because nothing django related should
be used in these tests:
`python manage.py test custom_code.tests.unit --settings=galactic_science_opm.settings_test`
or `pytest custom_code/tests/unit`

### Running integration tests

Since these might interact with the database, they should/must be run with
docker (docker exec), since e.g. hosts for databases and so on are set via envs
and also have no meaning outside the docker network:
`python manage.py test custom_code.tests.integration --settings=galactic_science_opm.settings_test`
or `pytest custom_code/tests/integration`

### Running e2e tests

To run E2E tests, you have to use the `compose.e2e.yaml`, so first use:
`docker compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml up -d`

This will also run the tests in the container `e2e`.

The start up will also run the management command `seed_e2e_data`, which clears
the test-database and adds testing data. For this to work, you have to put the
file `db_out_full.json` in the folder specified in the env variable
`DJANGO_TEST_DATA_DIR`. As this file might at some point contain data that is
proprietary, this file is not committed for now. This might change in the
future. To get this file, reach out to another dev.

Then you can run the tests on your machine, using
`pytest custom_code/tests/e2e -rs  --headed --slowmo=200`. This has the
advantage that you can see what the browser is doing and debug errors more
easily.

The tests can also be run headless on your machine, as they would in a CI setup
by using this command (locally or from docker):
`pytest custom_code/tests/e2e -rs`

Beware that running the E2E tests does **not** flush the test DB afterwards. So
any data that was created during the test, will remain in the database.

If you want to reset the test data right away, just visit `/flush_and_seed/`
when running the e2e setup and the test data will be reapplied.

When you run the E2E tests again, though, the database is reset and all the test
data is applied to the test database.

Or (but this has not been tested) to run this in some kind of CI setting:

```sh
docker compose -f compose.base.yaml -f compose.prod.yaml -f compose.e2e.yaml up \
--abort-on-container-exit --exit-code-from e2e
```

For help in creating tests, use `playwright codegen http://localhost:8000`.
