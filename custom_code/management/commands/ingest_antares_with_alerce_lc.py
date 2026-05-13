from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from custom_code.brokers import antares_alerce_combi
import numpy as np
from astropy import units as u

class Command(BaseCommand):

    help = 'Populate the database with lightcurves of ALeRCE ZTF microlensing candidates'

    def add_arguments(self, parser):
        parser.add_argument('days', help='days firstmjd before now')
        parser.add_argument('--phot', help='Force ingest of full photometry [optional]: True or False')

    def handle(self, *args, **options):
        print('Starting ANTARES microlensing filter target and photometry ingest')
        Antares = antares_alerce_combi.ANTARESBroker()
        full_phot = False
        if options['phot'] == str(True):
            full_phot = True

        # If a number of events to select is given, make a list of all available events;
        # the random selection is applied later.  If a specific event name is given, fetch data for that event only
        (list_of_targets, new_targets) = Antares.fetch_alerts(days=int(str(options['days'])))
        print('Identified '+str(len(list_of_targets))+' target(s) from ANTARES microlensing filter')
        if full_phot:
            Antares.find_and_ingest_photometry(list_of_targets)
        else:
            Antares.find_and_ingest_photometry(new_targets)
            
        print('Filtered and Identified '+str(len(list_of_targets))+' target(s) from ANTARES microlensing filter')
        print('Completed run of ANTARES microlensing filter event ingest')
