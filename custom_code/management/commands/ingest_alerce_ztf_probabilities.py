from django.core.management.base import BaseCommand
from custom_code.target_models import GalacticTarget, Classification
from django.db import transaction
import numpy as np
import pandas as pd
import datetime
from alerce.core import Alerce
from astropy.time import Time
from astropy import units as u
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class Command(BaseCommand):
    help = 'Populate the database with catalogs of known events and handle duplicates'

    def add_arguments(self, parser):
        parser.add_argument('target_name_contains', help='filter for targets containing ... (e.g. ZTF26)')

    def handle(self, *args, **options):
        #requires existing targets        
        time_window = timezone.now() - timedelta(days=20)
        new_or_modified_targets = GalacticTarget.objects.filter(
            Q(modified__gte=time_window) | 
            Q(reduceddatum__timestamp__gte=time_window)
        ).filter(name__icontains=str(options['target_name_contains'])).distinct()
        for target in new_or_modified_targets:
            print(f'Check lc_classifier_BHRF_forced_phot microlensing probability for event {target.name}')
            time_now = Time(datetime.datetime.now()).jd
            alerce = Alerce()
            probabilities = alerce.query_probabilities(target.name,survey='ztf')
            
            prob_pd = pd.DataFrame.from_dict(probabilities)
            prob_class1 = 0.
            prob_class2 = 0.
            try:
                stochastic_bhrf_prob = prob_pd.loc[prob_pd['classifier_name'] == 'lc_classifier_BHRF_forced_phot']
                prob_class1 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'Microlensing']['probability'].iloc[0])
                prob_class2 = float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'CV/Nova']['probability'].iloc[0])
            except Exception as e:
                print(f"Classification missing, Exception: {e}")
            prob_class3 = 0.
            try:
                bogus_prob = prob_pd.loc[prob_pd['classifier_name'] == 'stamp_classifier']
                prob_class3 = float(bogus_prob[bogus_prob['class_name'] == 'bogus']['probability'].iloc[0])
            except Exception as e:
                print(f"Classification missing, Exception: {e}")
            prob_class4 = 0.
            try:
                forced_atat_prob = prob_pd.loc[prob_pd['classifier_name'] == 'LC_classifier_ATAT_forced_phot(beta)']
                prob_class4 = float(forced_atat_prob[forced_atat_prob['class_name'] == 'Microlensing']['probability'].iloc[0])
            except Exception as e:
                print(f"Classification missing, Exception: {e}")
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
                if prob_class1>0 or prob_class2>0:
                    with transaction.atomic():
                        m = Classification.objects.update_or_create(target=target,
                                                        source='ALeRCE_ZTF',
                                                        class1='microlensing',
                                                        prob_class1 = prob_class1,
                                                        class2='cv/nova',
                                                        prob_class2 = prob_class2,
                                                        class3='bogus',
                                                        prob_class3 = prob_class3,
                                                        class4='microlensing_atat',
                                                        prob_class4 = prob_class4
                                                        )
            except Exception as e:
                print(f"Exception: {e}")
            
        print('probabilities created/updated.')
