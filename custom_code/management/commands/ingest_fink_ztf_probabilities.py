from django.core.management.base import BaseCommand
from django.apps import apps
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from sklearn.preprocessing import QuantileTransformer
from os import path
import numpy as np
import pandas as pd
import datetime
import joblib

from astropy.time import Time, TimezoneInfo
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):
    help = 'Populate the database with rescaled fink probabilities'

    def add_arguments(self, parser):
        parser.add_argument('nevents', help='Number of events to be ingested')

    def handle(self, *args, **options):
        #load quantile transformer fit prepared with QuantileTransformer(output_distribution="uniform", random_state=0)

        #qt_fink = QuantileTransformer(output_distribution="uniform", random_state=0)
        #qt_fink.fit_transform(dist_fink.reshape(-1, 1)).flatten()
        #filename = 'quantile_transformer_fink.joblib'
        #joblib.dump(qt_fink, filename)
        app_config = apps.get_app_config('custom_code')
        #start configuration for ZTF, pill serialized trafos can be stored on a 
        #daily basis, for instance.
        file_path = path.join(app_config.path, 'auxiliary_data/quantile_transformer_fink.joblib')
        try:        
            loaded_qt = joblib.load(file_path)
            trafo_loaded = True
        except:
            print("Could not open file")
            trafo_loaded = False
  

        #For galactic opm, remove known galaxies
        no_galaxies = pdf['d:cdsxmatch'] != 'Galaxy'
        pdf_no_galaxies = pdf[no_galaxies]
        if trafo_loaded:
            pdf_no_galaxies["d:mulens_uniform"] = loaded_qt.transform(np.array(pdf_no_galaxies["d:mulens"]).reshape(-1, 1))        
     
     #   m = Classification.objects.update_or_create(target=target,
     #                                               source='fink_ZTF',
     #                                               class1='microlensing',
     #                                               prob_class1 = prob_class1,
     #                                               class2='cv/nova',
     #                                              prob_class2 = prob_class2)
     #       
     #   print('probabilities created/updated.')