from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from custom_code.brokers import microlensing_survey_coords

class Command(BaseCommand):

    help = 'Populate the database with coordinates of targets from OGLE, KMTNet, MACHO, EROS2'
    #MOAPRIME tbd

    def add_arguments(self, parser):
        parser.add_argument('years', help='years to harvest, separated by , (used for OGLE/KMTNet)')
        parser.add_argument('surveys', help='survey(s) to ingest: all, or comma-separated list of OGLE,KMTNET,MACHO,EROS2')

    def handle(self, *args, **options):
        print('Start survey ingest')
        broker = microlensing_survey_coords.MicrolensingCoordsBroker()

        if ',' in options['years']:
            year_list = options['years'].split(',')
        else:
            year_list = [options['years']]

        if ',' in options['surveys']:
            survey_list = options['surveys'].split(',')
        elif options['surveys'].lower() == 'all':
            survey_list = 'all'
        else:
            survey_list = [options['surveys']]
            
        results = broker.fetch_alerts(years=year_list, surveys=survey_list)

        for survey, (list_of_targets, new_targets) in results.items():
            print(f'{survey}: ingested {len(list_of_targets)} target(s), {len(new_targets)} new')
            
        print('Completed run of coordinate-only survey ingest')
