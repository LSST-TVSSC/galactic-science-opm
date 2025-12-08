from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from tom_dataproducts.models import ReducedDatum
from custom_code.match_managers import validators
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.time import Time, TimezoneInfo

class Command(BaseCommand):

    help = 'ingest photometry from file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', help='Path to file of events to ingest')
        parser.add_argument('filter', help='filter, e.g. OGLE_I, ZTF_g: ')        
        parser.add_argument('target', help='target name')

    def handle(self, *args, **options):

        # Load catalog file of events, assuming a file structure like OGLE phot.dat
        photometry = np.loadtxt(options['file_path'])
        qs = GalacticTarget.objects.filter(name__icontains=options['target'])
        if len(qs) == 1:
            target = qs[0]
            print(qs)
            for row in photometry:
                print(row)
                jd = Time( float(row[0]), format='jd', scale='utc')
                jd.to_datetime(timezone=TimezoneInfo())
                datum = {'magnitude': float(row[1]),
                        'filter': options['filter'],
                        'error': float(row[2]),
                        }
                print(datum)
            try:
                rd, created = ReducedDatum.objects.get_or_create(
                    timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                    value=datum,
                    source_name='UPLOAD',
                    source_location=target.name,
                    data_type='photometry',
                    target=target)

            except Exception as e:
                print('Could not ingest '+target.name+' '+e)

            target.save()

        return 'OK'
