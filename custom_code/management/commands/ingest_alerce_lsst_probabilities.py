from django.core.management.base import BaseCommand
from custom_code.helpers import create_and_attach_classifications_to_target
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
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
        #requires existing targets, LSST ids will not be identifiable
        qs = GalacticTarget.objects.filter(name__icontains=str(options['target_name_contains']))
        target_list = list(set(qs))
        if len(target_list) == 0:
            print(f"Target list for name '{options["target_name_contains"]}' was empty. Stopping.")
            return

        for target in target_list:
            print('Check lc_classifier_BHRF_forced_phot microlensing probability for event ' + target.name)
            time_now = Time(datetime.datetime.now()).jd
            alerce = Alerce()
            probabilities = alerce.query_probabilities(target.name,survey='lsst')
            
            prob_pd = pd.DataFrame.from_dict(probabilities)
            stochastic_bhrf_prob = prob_pd.loc[prob_pd['classifier_name'] == 'lc_classifier_BHRF_forced_phot']
            try:
                prob_class1=float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'Microlensing']['probability'].iloc[0])
            except:
                prob_class1=0.
            try:
                prob_class2=float(stochastic_bhrf_prob[stochastic_bhrf_prob['class_name'] == 'CV/Nova']['probability'].iloc[0])
            except:
                prob_class2=0.
            try:
                bogus_prob = prob_pd.loc[prob_pd['classifier_name'] == 'stamp_classifier']
                prob_class3 = float(bogus_prob[bogus_prob['class_name'] == 'bogus']['probability'].iloc[0])
            except:
                prob_class3=0.
            print(target.name,'microlensing prob ALeRCE ', stochastic_bhrf_prob, prob_class1, ' bogus ',prob_class3)
            try:
                #For ZTF events ingest fink probability as maximum probability 
                #attach it to the ALeRCE query to avoid repeating the galactic target filter.
                r = requests.post(
                "https://api.fink-portal.org/api/v1/objects",
                json={"objectId": str(target.name), "output-format": "json"})
                pdf_fink = pd.read_json(io.BytesIO(r.content))
                if len(r.content) >2:
                    new_pdf_fink = pdf_fink[["i:jd", "d:mulens"]].copy()
                    m = Classification.objects.update_or_create(target=target,
                                                  source='fink_LSST',
                                                  class1='microlensing',
                                                  prob_class1 = np.max(new_pdf_fink["d:mulens"]))
                    print(target.name,'microlensing prob fink ', np.max(new_pdf_fink["d:mulens"]))
                else:
                    print("No fink classification in lightcurve, yet.")
            except Exception as e:
                print("Fink request not successful for ", target.name, e)

            m = Classification.objects.update_or_create(target=target,
                                              source='ALeRCE_LSST',
                                              class1='microlensing',
                                              prob_class1 = prob_class1,
                                              class2='cv/nova',
                                              prob_class2 = prob_class2,
                                              class3='bogus',
                                              prob_class3 = prob_class3
                                              )
            # add new classifications
            try:
                _, classifications = create_and_attach_classifications_to_target(probabilities=probabilities, target=target)
                print(f"Added {len(classifications)} for target {target}.")
            except Exception as e:
                print(f"Something went wrong creating and attaching classifications for target {target}")
                print(e)

            
        print('probabilities created/updated.')
