import os
import sys
from django.core.management import execute_from_command_line

def run_ztf26():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'galactic_science_opm.settings')
    #ingest lightcurves makes the event query
    #just in case, test ingest of LSST is called
    commands = [
        ['./manage.py','ingest_alerce_ztf_lightcurves','ZTF26','1','1'],
        ['./manage.py','ingest_antares_with_alerce_lc','3'],
        ['./manage.py','ingest_alerce_ztf_probabilities','T','3'],
        ['./manage.py','run_rtmodel_fits','T'],
        ['./manage.py','run_probability_rescaling','T']
    ]

    for command in commands:
        print(f"Running command: {command}")
        try:
            execute_from_command_line(command)
        except Exception as e:
            print(f"Error running: {command} - {e}")

def run_lsst26():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'galactic_science_opm.settings')
    #ingest lightcurves makes the event query
    #just in case, test ingest of LSST is called
    commands = [
        ['./manage.py','ingest_alerce_lsst_lightcurves','1','1'],
        ['./manage.py','ingest_alerce_lsst_probabilities',''],
    ]

    for command in commands:
        print(f"Running command: {command}")
        try:
            execute_from_command_line(command)
        except Exception as e:
            print(f"Error running: {command} - {e}")

if __name__ == "__main__":
    run_ztf26()
