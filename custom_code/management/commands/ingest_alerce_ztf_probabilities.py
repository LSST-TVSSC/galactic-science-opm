from django.core.management.base import BaseCommand
from custom_code.helpers import create_and_attach_classifications_to_target
from custom_code.helpers import create_and_attach_classifications_to_target_antares
from custom_code.target_models import GalacticTarget, Classification
from django.db import transaction
import numpy as np
import pandas as pd
import datetime
from alerce.core import Alerce
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from antares_client.search import get_by_lsst_dia_object_id, get_by_ztf_object_id

class Command(BaseCommand):
    help = 'Populate the database with catalogs of known events and handle duplicates'

    def add_arguments(self, parser):
        parser.add_argument('target_name_contains', help='filter for targets containing ... (e.g. ZTF26)')
        parser.add_argument('days', help='modified n days before now, e.g. 2')

    def handle(self, *args, **options):
        #requires existing targets        
        time_window = timezone.now() - timedelta(days=int(str(options['days'])))
        new_or_modified_targets = GalacticTarget.objects.filter(
            Q(modified__gte=time_window) | 
            Q(photometryreduceddatum__timestamp__gte=time_window)
        ).filter(name__icontains=str(options['target_name_contains'])).distinct()

        if len(new_or_modified_targets) == 0:
            print("Neither new nor modified targets to check were found. Stopping.")
            return
        
        for target in new_or_modified_targets:
            print(f'Check lc_classifier_BHRF_forced_phot microlensing probability for event {target.name}')
            alerce = Alerce()
            try:
                if "ZTF" in "".join( [x for x in target.names if "ZTF" in x]):
                    target_name_ztf =  [x for x in target.names if "ZTF" in x][0]
                    probabilities = alerce.query_probabilities(target_name_ztf,survey='ztf')
                    try: 
                        antares_locus =  get_by_ztf_object_id(str(target_name_ztf))
                        if "feature_antares_devkit_version" in antares_locus.properties:
                            antares_version = antares_locus.properties["feature_antares_devkit_version"]
                        else:
                            antares_version = "0.0"
                        antares_probability = 0.0          
                        chi2_red_keys = [antares_locus.properties[x] for x in antares_locus.properties if "chi2" in x and "microlensing" in x]
                        if len(chi2_red_keys)>0:
                            print(chi2_red_keys,target)
                            antares_probability = np.mean(chi2_red_keys)
                    except Exception as e:
                        print(f"Could not ingest ANTARES filter data {e}.")

                elif "LSST" in "".join( [x for x in target.names if "LSST" in x]):
                    target_name_lsst =  [x for x in target.names if "LSST" in x][0]
                    probabilities = alerce.query_probabilities(target_name_lsst[5:],survey='lsst')
                    try: 
                        antares_locus = get_by_lsst_dia_object_id(str(target_name_lsst[5:]))
                        if "feature_antares_devkit_version" in antares_locus.properties:
                            antares_version = antares_locus.properties["feature_antares_devkit_version"]
                        else:
                            antares_version = "unknown"
                        antares_probability = 0.0                       
                        chi2_red_keys = [antares_locus.properties[x] for x in antares_locus.properties if "chi2" in x and "microlensing" in x]
                        if len(chi2_red_keys)>0:
                            print(chi2_red_keys,target)

                            antares_probability = np.mean(chi2_red_keys)
                    except Exception as e:
                        print(f"Could not ingest ANTARES filter data {e}.")
                else:
                    print(f"No probability ingested {target.names}")
                    continue
            except Exception as e:
                print(f"No probability ingested {e}")
                continue
            try:
                if "ZTF" in "".join( [x for x in target.names if "ZTF" in x]):
                    best_class = max([(item['probability'],item['class_name'],
                                      item['classifier_name']) for item in probabilities if
                                      'lc_classifier_BHRF_forced_phot' == item['classifier_name']])[1]
                else:
                    best_class = max([(item['probability'],item['class_name'],
                                      item['classifier_name']) for item in probabilities if
                                      'stamp_classifier_rubin_beta' == item['classifier_name']])[1]
                print(best_class)
                with transaction.atomic():
                    GalacticTarget.objects.filter(name=target).update(target_type=f"{best_class} candidate")
            except Exception as e:
                print(f"Exception: {e}")
                best_class = ""

            if "Microlensing" in best_class:
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
            else:
                #Mostly affects ANTARES filter events with differing ALeRCE classification
                prob_class1 = 1e-99
                prob_class2 = 0.
                prob_class3 = 0.
                prob_class4 = 0.
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

            # add new classifications ALeRCE
            try:
                _, new_classification, updated_classifications = (
                    create_and_attach_classifications_to_target(
                        probabilities=probabilities, target=target
                    )
                )
                print(
                    f"Added {len(new_classification)} and updated {len(updated_classifications)} classifications for target {target}."
                )
            except Exception as e:
                print(
                    f"Something went wrong creating and attaching classifications for target {target}"
                )
                print(e)
            # add new classifications ANTARES microlensing filter        
            try:
                _, new_classification, updated_classifications = (
                    create_and_attach_classifications_to_target_antares(target,antares_probability,antares_version)
                )
                print(
                    f"Added {len(new_classification)} and updated {len(updated_classifications)} classifications for target {target} ANTARES filter."
                )
            except Exception as e:
                print(
                    f"Something went wrong creating and attaching classifications for target {target} ANTARES filter"
                )
                print(e)
            
        print('probabilities created/updated.')
