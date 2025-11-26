from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u


class Command(BaseCommand):

    help = 'Populate the database with lightcurves'

    def add_arguments(self, parser):
        parser.add_argument('file_path', help='Path to file lightcurve to ingest')
        parser.add_argument('event', help='event name')

    def handle(self, *args, **options):

        # Load catalog file of events
        if ".csv" in options['file_path']:
            light_curve = pd.read_csv(options['file_path'])
        elif ".dat" in options['file_path']:
            light_curve = np.loadtxt(options['file_path'])
            


