from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from custom_code.brokers import ogle
import numpy as np
from astropy import units as u

class Command(BaseCommand):

    help = 'Populate the database with lightcurves of known OGLE events - all or for a given year'

    def add_arguments(self, parser):
        parser.add_argument('years', help='years you want to harvest, separated by ,')
        parser.add_argument('events', help='name of a specific event, all or an integer number')
        parser.add_argument('--phot', help='Force ingest of full photometry [optional]: True or False')


    def handle(self, *args, **options):
        print('Starting OGLE photometry ingest')
        Ogle = ogle.OGLEBroker()
        # Parse the years for which to harvest target data, since this could be a single
        # integer or a list:
        if ',' in options['years']:
            year_list = options['years'].split(',')
        else:
            year_list = [options['years']]
        full_phot = False
        if options['phot'] == True:
            full_phot = True

        # If a number of events to select is given, make a list of all available events;
        # the random selection is applied later.  If a specific event name is given, fetch data for that event only
        (list_of_targets, new_targets) = Ogle.fetch_alerts(years=year_list, events=str(options['events']))

        print('Identified and ingested '+str(len(list_of_targets))+' target(s) from OGLE survey')

        # The following random selection is made to avoid the harvesting process taking so long
        # that the Kubernetes pod times out.  By randomizing the target selection, we ensure
        # that all targets should be updated quite often through more frequent runs of this harvester
        if str(options['events']).isnumeric():
            selected_targets = Ogle.select_random_targets(list_of_targets, new_targets, ntargets=int(options['events']))
            print('Ingesting data from '+str(len(selected_targets))+' randomly-selected targets')
        else:
            selected_targets = Ogle.sort_target_list(list_of_targets)
            print('Ingesting data from '+str(len(selected_targets))+' selected targets')

        Ogle.find_and_ingest_photometry(selected_targets, full_phot=full_phot)

        print('Completed run of OGLE event ingest')
