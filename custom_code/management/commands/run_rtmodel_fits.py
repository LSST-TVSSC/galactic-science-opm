from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
from django.db import transaction
from astropy.time import Time
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
import datetime
import os
import numpy as np
from django.db import connection

class Command(BaseCommand):
    help = 'Fit events with PSPL and parallax, then ingest fit parameters in MicrolensingModel'

    def add_arguments(self, parser):
        parser.add_argument('event', help='Eventname')

    def handle(self, *args, **options):
        target = Target.objects.get(name=str(options['event']))
        target_id = target.id

        with transaction.atomic():
            photometry = ReducedDatum.objects.filter(data_type='photometry', target=target).order_by('-timestamp')
            data = []
            for reduced_datum in photometry:
                rd_data = {'timestamp': reduced_datum.timestamp}
                if 'limit' in reduced_datum.value.keys():
                    rd_data['magnitude'] = reduced_datum.value['limit']
                    rd_data['limit'] = True
                else:
                    rd_data['magnitude'] = reduced_datum.value['magnitude']
                    rd_data['limit'] = False
                data.append(rd_data)
            print(data)

if __name__ == '__main__':
    main()
