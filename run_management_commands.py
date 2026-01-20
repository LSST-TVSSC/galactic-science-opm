import os
import sys
from django.core.management import execute_from_command_line

def run_ztf26():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'galactic_science_opm.settings')

    commands = [
        ['./manage.py','ingest_alerce_ztf_probabilities','ZTF26'],
        ['./manage.py','ingest_alerce_ztf_lightcurves','ZTF26','30','30'],
        ['./manage.py','run_rtmodel_fits','all'],
        ['./manage.py','run_probability_rescaling','ZTF26']
    ]

    for command in commands:
        print(f"Running command: {command}")
        try:
            execute_from_command_line(command)
        except Exception as e:
            print(f"Error running: {command} - {e}")

if __name__ == "__main__":
    run_ztf26()
