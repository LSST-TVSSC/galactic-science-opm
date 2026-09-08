from django.core.management.base import BaseCommand
from astropy.time import Time, TimezoneInfo
from custom_code.catalogs.GladePlusApiClient import GladeClientApi
from custom_code.observations.HealpyExpectedVisitsClient import HealpyExpectedVisitsClient
from custom_code.photometry.AlercePhotometryClient import AlercePhotometryClient
from custom_code.photometry.PhotometryCreator import PhotometryCreator
from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.brokers import alerce_ztf
from custom_code.targets.AlerceApiClient import AlerceApiClient
from custom_code.targets.AlerceZtfLightcurvesPipeline import AlerceZtfLightcurvesPipeline
from custom_code.targets.TargetCreator import TargetCreator
from custom_code.variability.VizierVariabilityFlagsClient import VizierVariabilityFlagsClient

class Command(BaseCommand):

    help = 'Populate the database with lightcurves of ALeRCE ZTF microlensing candidates'

    def add_arguments(self, parser):
        parser.add_argument('event_name', help='Either event name or substring the events should contain')
        parser.add_argument('survey', help='The survey for which to look')
        parser.add_argument('days', help='days firstmjd before now')
        parser.add_argument('phot', help='Force ingest of full photometry [optional]: True or False')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Alerce-Ztf-Lightcurves pipeline"))

        if options['phot'] == str(True):
            full_phot = True
        else:
            full_phot = False
        since_n_days = int(str(options['days']))
        event_name = options['event_name']
        survey = options['survey']

        def logger(style, message):
            self.stdout.write(self.style.SUCCESS(message))

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=AlerceApiClient(),
            target_creator=TargetCreator(),
            glade_api_client=GladeClientApi(),
            visits_checker=HealpyExpectedVisitsClient(),
            variability_checker=VizierVariabilityFlagsClient(),
            photometry_fetcher=AlercePhotometryClient(),
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey=survey,
            start_date=int(Time.now().mjd),
            since_n_days=since_n_days,
            fetch_photometry_for_all_targets=full_phot,
            event_name=event_name
        )

        self.stdout.write(self.style.SUCCESS("Alerce-Ztf-Lightcurves pipeline done."))
