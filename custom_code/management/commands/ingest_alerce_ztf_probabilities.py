from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from django.apps import apps
import joblib
from sklearn.preprocessing import QuantileTransformer
import numpy as np
import pandas as pd
import datetime
from alerce.core import Alerce
from astropy.time import Time, TimezoneInfo
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):
    help = 'Populate the database with catalogs of known events and handle duplicates'

    def add_arguments(self, parser):
        parser.add_argument('target_name_contains', help='filter for targets containing ... (e.g. ZTF25)')

    def handle(self, *args, **options):

        app_config = apps.get_app_config('custom_code')
        file_path = path.join(app_config.path, 'auxiliary_data/quantile_transformer_alerce.joblib')
        try:        
            loaded_qt = joblib.load(file_path)
            trafo_loaded = True
        except:
            print("Could not open file")
            trafo_loaded = False

        qs = GalacticTarget.objects.filter(name__icontains=str(options['target_name_contains']))
        target_list = list(set(qs))

        for target in target_list:
            print('Check lc_classifier_BHRF_forced_phot microlensing probability for event ' + target.name)
            time_now = Time(datetime.datetime.now()).jd
            alerce = Alerce()
            probabilities = alerce.query_probabilities(target.name)
            
            prob_pd = pd.DataFrame.from_dict(probabilities)
            stochastic_bhrf_prob = prob_pd.loc[prob_pd['classifier_name'] == 'lc_classifier_BHRF_forced_phot']
            prob_class1 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'Microlensing']['probability'].iloc[0])
            prob_class2 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'CV/Nova']['probability'].iloc[0])
            
            m = Classification.objects.update_or_create(target=target,
                                              source='ALeRCE_ZTF',
                                              class1='microlensing',
                                              prob_class1 = prob_class1,
                                              class2='cv/nova',
                                              prob_class2 = prob_class2)
            
        print('probabilities created/updated.')
