from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from custom_code.brokers import alerce_ztf
import numpy as np
from astropy import units as u

class Command(BaseCommand):

    help = 'Populate the database with a single lightcurve of ALeRCE ZTF event'

    def add_arguments(self, parser):
        parser.add_argument('event_name', help='Either event name or substring the events should contain')

    def handle(self, *args, **options):
        print('Starting ALeRCE single event photometry ingest')
        Alerce = alerce_ztf.ALERCEBroker()
        (list_of_targets, new_targets) = Alerce.fetch_alert(str(options['event_name']))
        Alerce = alerce_ztf.ALERCEBroker()
        Alerce.find_and_ingest_photometry(list_of_targets)
        print('Completed single run of ALeRCE event ingest')
