from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from django.db import transaction
import numpy as np
import pandas as pd
import requests, io
import datetime
from alerce.core import Alerce
from astropy.time import Time, TimezoneInfo
from astropy.coordinates import SkyCoord
from astropy import units as u

class Command(BaseCommand):
    help = 'Populate the database with catalogs of known events and handle duplicates'

    def add_arguments(self, parser):
        parser.add_argument('target_name_contains', help='filter for targets containing ... (e.g. ZTF26)')

    def handle(self, *args, **options):
        #requires existing targets
        qs = GalacticTarget.objects.filter(name__icontains=str(options['target_name_contains']))
        target_list = list(set(qs))
        for target in target_list:
            print('Check lc_classifier_BHRF_forced_phot microlensing probability for event ' + target.name)
            time_now = Time(datetime.datetime.now()).jd
            alerce = Alerce()
            probabilities = alerce.query_probabilities(target.name,survey='ztf')
            
            prob_pd = pd.DataFrame.from_dict(probabilities)
            stochastic_bhrf_prob = prob_pd.loc[prob_pd['classifier_name'] == 'lc_classifier_BHRF_forced_phot']
            prob_class1 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'Microlensing']['probability'].iloc[0])
            prob_class2 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'CV/Nova']['probability'].iloc[0])
            
            try:
                bogus_prob = prob_pd.loc[prob_pd['classifier_name'] == 'stamp_classifier']
                prob_class3 = float(bogus_prob[bogus_prob['class_name'] == 'bogus']['probability'].iloc[0])
            except:
                prob_class3=0
#            try:
                #For ZTF events ingest fink probability as maximum probability 
                #attach it to the ALeRCE query to avoid repeating the galactic target filter.
#Deactivated, until Stream is online.
#                r = requests.post(
#                "https://api.fink-portal.org/api/v1/objects",
#                json={"objectId": str(target.name), "output-format": "json"})
#                pdf_fink = pd.read_json(io.BytesIO(r.content))
#                if len(r.content) >2:
#                    new_pdf_fink = pdf_fink[["i:jd", "d:mulens"]].copy()
#                    with transaction.atomic():
#                        m = Classification.objects.update_or_create(target=target,
#                                                      source='fink_ZTF',
#                                                      class1='microlensing',
#                                                      prob_class1 = np.max(new_pdf_fink["d:mulens"]))
#                else:
#                    print("No fink classification in lightcurve, yet.")
#            except Exception as e:
#                print("Fink request not successful for ", target.name, e)
        try:
            with transaction.atomic():
                m = Classification.objects.update_or_create(target=target,
                                                  source='ALeRCE_ZTF',
                                                  class1='microlensing',
                                                  prob_class1 = prob_class1,
                                                  class2='cv/nova',
                                                  prob_class2 = prob_class2,
                                                  class3='bogus',
                                                  prob_class3 = prob_class3
                                                  )
        except Exception as e:
            print(f"Exception: {e}")
            
        print('probabilities created/updated.')
