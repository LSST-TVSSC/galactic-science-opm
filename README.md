# Observation Priority Manager (OPM)

The Observation Priority Manager (OPM) for Galactice Science in the TVSSC.

# Observational Planning/Priority Manager (OPM) - A Target and Observation Manager Instance for the TVS galactic science community

The OPM is an instance of the Target and Observation Manager ([TOM Toolkit](https://tom-toolkit.readthedocs.io/en/stable/)) designed to track galactic science alerts over time, ingest targets with their alert priority, display corresponding light curves, and communicate with other TOM systems connected to observatories and proposals. This repository provides a system that can be installed locally by members of the TVS galactic science community, for instance the Microlensing Subgroup, and eventually deployed in a suitable cloud environment.

## Usage
Once installed, you can access and interact with the OPM through its web interface. Here are some key features of the system:
* **Target Management**: Create, view, and update targets associated with microlensing alerts, subscribe to broker services
* **Light Curve Visualization**: View and analyze light curves associated with each target to monitor microlensing events over time.

## Planned Features
* **Communication with Other TOM Systems**: Interact with other TOM systems connected to observatories and proposals, enabling easy requesting of observations directly from the OPM interface.
* **Requesting and interacting with HPC systems to fit events**: Interact safely with HPC centers to fit complicated microlensing events, i.e. binary and triple lens events
# Quick start

After cloning the repository and changing your directory in to the cloned repo:
```bash
docker compose up -d
```
will, according to the `compose.yaml` file,  build a docker image, run it in a container, using a Postgresql database running in another container. Point your browser to http://127.0.0.1:8000 for the Galactic Science OPM home page running locally.

When the database is empty, you may want to create an admin user for your TOM. You can do so by running the Django `createsuperuser` management command in the the container. First 'exec' into the container:
```bash
docker exec -it galactic-science-opm-galactic-science-opm-1 /bin/bash
```
In the container's bash shell (that you just openned):
```bash
./manage.py createsuperuser
```
Ctrl-d to leave the container. Log into the OPM with the credentials you just created.

To stop the containers:
```bash
docker compose down
```

# Setting up for local development
After cloning the repository and changing your directory (`cd`-ing) into the cloned repo:

## 1. Create a virtual environment
Always work in a virtual enviroment. To create and activate one:
```bash
python -m venv .venv
source .venv/bin/activate
```

## 2. Install the dependencies
There are more than one way to do this. The `pyproject.toml` project description file is common to all of them. Here, we use `poetry`:
```bash
poetry install
```

## 3. Work in a branch for the development that you'll be doing
If you've just cloned the repo, you'll be in the `dev` branch. You'll want to do your development in a branch that can later be merged into the `dev` branch (and ultimately into the `main` branch for deployment). With the `-b` switch, `git checkout` creates a new branch.If the branch you want already exists, you don't need the `-b` switch.

```bash
git checkout -b <name-of-your-branch>
```

## 4. Spin up a database for your development OPM to use
We quote from [settings.py](https://github.com/LSST-TVSSC/galactic-science-opm/blob/c0d47f68bd4ed2d8721ef3b0cf900eb5ae75a81e/galactic_science_opm/settings.py#L113):
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

## 5. Start the Django development server
```bash
./manage.py runserver
```
Point your browser to http://127.0.0.1:8000 for the Galactic Science OPM home page running locally.




