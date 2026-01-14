from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
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
        
            bogus_prob = prob_pd.loc[prob_pd['classifier_name'] == 'stamp_classifier']
            prob_class3 = float(bogus_prob[bogus_prob['class_name'] == 'bogus']['probability'].iloc[0])
            m = Classification.objects.update_or_create(target=target,
                                              source='ALeRCE_ZTF',
                                              class1='microlensing',
                                              prob_class1 = prob_class1,
                                              class2='cv/nova',
                                              prob_class2 = prob_class2,
                                              class3='bogus',
                                              prob_class3 = prob_class3
                                              )
            
        print('probabilities created/updated.')
