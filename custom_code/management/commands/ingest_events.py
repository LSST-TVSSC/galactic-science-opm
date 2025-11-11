from django.core.management.base import BaseCommand
from tom_targets.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):

    help = 'Populate the database with catalogs of known events and handle duplicates'

    def add_arguments(self, parser):
        parser.add_argument('file_path', help='Path to file of events to ingest')
        parser.add_argument('source', help='Origin of the event detection, e.g. survey name')

    def handle(self, *args, **options):

        # Load catalog file of events
        with open(options['file_path'], 'r') as f:
            file_lines = f.readlines()

            # Skip the first line for the file header
            for entry in file_lines[1:]:
                event_name = entry[0]
                ra = entry[1]
                dec = entry[2]
                t0 = entry[3]
                tE = entry[4]
                u0 = entry[5]
                base_i_mag = entry[6]
                err_i_mag = entry[7]

                # First check that the event isn't already known by name
                qs = Target.objects.filter(name=event_name)

                # If not, proceed with duplication check based on position
                if len(qs) == 0:
                    s = SkyCoord(ra, dec, unit=(u.hourangle, u.deg), frame='icrs')

                    # If baseline photometry is available, include it
                    if 'none' not in str(base_i_mag).lower():
                        base_i_mag = float(base_i_mag)
                    else:
                        base_i_mag = 0.0
                    if 'none' not in str(err_i_mag).lower():
                        err_i_mag = float(err_i_mag)
                    else:
                        err_i_mag = 0.0

                    target, result = validators.get_or_create_event(
                        event_name,
                        s.ra.deg,
                        s.dec.deg,
                        base_i_mag,
                        err_i_mag,
                        'microlensing',
                        debug=debug
                    )

                    # If the target is new, ingest other parameters
                    if result == 'new_target':

                        # Create classification as microlensing
                        c = Classification.objects.create(
                            target=target,
                            source=options['source'],
                            class1='microlensing'
                        )

                        # Ingest event model parameters, if available,
                        if 'none' not in str(t0).lower() \
                            and 'none' not in str(tE).lower() \
                            and 'none' not in str(u0).lower():

                            m = MicrolensingModel.objects.create(
                                target=target,
                                t0=float(t0),
                                tE=float(tE),
                                u0=float(u0)
                            )

