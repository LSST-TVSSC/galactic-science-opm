import os
import sys
from django.core.management import execute_from_command_line

def run_init():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'galactic_science_opm.settings')

    commands = [
        ['./manage.py','ingest_ogle_lightcurves','2022','all','--phot=True'],
        ['./manage.py','ingest_ogle_lightcurves','2023','all','--phot=True'],
#        ['./manage.py','ingest_alerce_ztf_lightcurves','ZTF24','60','60'],
         ['./manage.py','ingest_alerce_ztf_lightcurves','ZTF25','60','60','--phot=True'],
#        ['./manage.py','ingest_alerce_ztf_probabilities','ZTF24'],
#         ['./manage.py','ingest_alerce_ztf_probabilities','ZTF25'],
#        ['./manage.py','run_probability_rescaling','ZTF24'],
#         ['./manage.py','run_probability_rescaling','ZTF25']
    ]

    for command in commands:
        print(f"Running command: {command}")
        try:
            execute_from_command_line(command)
        except Exception as e:
            print(f"Error running: {command} - {e}")

if __name__ == "__main__":
    run_init()
