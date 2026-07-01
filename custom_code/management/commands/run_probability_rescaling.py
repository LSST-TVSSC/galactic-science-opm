from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
from custom_code.target_models import GalacticTarget, Classification, MicrolensingRadarData
from custom_code.target_models import MicrolensingParameterModel, ClassificationGeneralized, ClassificationSource
import numpy as np
import healpy as hp
from ._rescale_ztf_microlensing_prob import psi_planet_priority_peak

class Command(BaseCommand):
    help = 'Populate the database with updated master probability based on '

    def add_arguments(self, parser):
        parser.add_argument('target_name_contains', help='filter for targets containing ... (e.g. ZTF2X), LSST, OGLE')

    def handle(self, *args, **options):
        qs = GalacticTarget.objects.filter(name__icontains=str(options['target_name_contains']))
        target_list = list(set(qs))

        config = apps.get_app_config('custom_code')

        model_qt_psi = config.model_qt_psi
        model_qt_fink = config.model_qt_fink
        model_qt_alerce = config.model_qt_alerce
        model_qt_alerce_atat = config.model_qt_alerce_atat
        hpx_map = config.nsquare_map
        visit_map = config.nvisits_10yrs_map
        nside  = config.nside
        for target in target_list:
            
            class_versions = (
                ClassificationGeneralized.objects
                .filter(target_id=target)
                .filter(source__classifier_name="lc_classifier_BHRF_forced_phot")
                .values_list('source__classifier_version', flat=True)
                .distinct()
            )

            if len(class_versions)>0:
                highest_version = max(
                    class_versions, 
                    key=lambda v: [int(x) for x in v.split('.')]
                )
                
                latest_probabilities = (
                    ClassificationGeneralized.objects
                    .filter(target_id=target)
                    .filter(source__classifier_name="lc_classifier_BHRF_forced_phot")
                    .filter(source__classifier_version=str(highest_version))
                    .order_by('name', '-updated_at').distinct('name')
                )           
                ratio_numerator = 0.
                ratio_denominator = 0.
                try:
                    for entry in latest_probabilities:
                        if entry.source.class_name != "Microlensing":
                            ratio_denominator += float(entry.probability)
                        else:
                            ratio_numerator = float(entry.probability)
                
                    if ratio_denominator == 0.:
                        prob_contrast = 1.
                    else:
                        ratio = ratio_numerator/ratio_denominator
                        prob_contrast = ratio/(1+ratio)
                except Exception as e:
                    print("no microlensing prob contrast available.")
                    prob_contrast = 0.
            else:
                prob_contrast = 0.

            class_versions = (
                ClassificationGeneralized.objects
                .filter(target_id=target)
                .filter(source__classifier_name="microlensing_filter")
                .values_list('source__classifier_version', flat=True)
                .distinct()
            )

            if len(class_versions)>0:
                
                try:
                    highest_version = max(
                        class_versions, 
                        key=lambda v: [int(x) for x in v.split('.')]
                    )
                except:
                    highest_version = "unknown"
                 
                latest_probabilities = (
                    ClassificationGeneralized.objects
                    .filter(target_id=target)
                    .filter(source__classifier_name="microlensing_filter")
                    .filter(source__classifier_version=str(highest_version))
                    .order_by('name', '-updated_at').distinct('name')
                )    
                prob_red_chisqr_antares = 0.       
                try:
                    prob_red_chisqr_antares = min(latest_probabilities[0].probability,1/latest_probabilities[0].probability)
                except Exception as e:
                    print("no microlensing red_chisqr available.")

            microlensing_model = MicrolensingParameterModel.objects.filter(target=target)
            if not microlensing_model.exists():
                continue
            else:
                microlensing_model = MicrolensingParameterModel.objects.filter(target=target).latest()

            target_classification = Classification.objects.filter(target=target)

            if target_classification.exists():
                try:
                    psip = psi_planet_priority_peak(microlensing_model.u0, microlensing_model.err_u0,
                                                    microlensing_model.tE, microlensing_model.err_tE, 
                                                    sigma_threshold = 0.5)
                    reshaped_value = np.array([[psip]])
                    transformed_prob_planet = model_qt_psi.transform(reshaped_value)
                    if np.isnan(transformed_prob_planet[[0]]):
                        transformed_prob_planet = [[0]]
                except:
                    transformed_prob_planet = [[0]]

                if target_classification.filter(source="fink_ZTF").exists():
                    try:
                        prob_fink = target_classification.filter(source="fink_ZTF").latest().prob_class1
                        reshaped_value = np.array([[prob_fink]])
                        transformed_prob_fink = model_qt_fink.transform(reshaped_value)
                    except:
                        transformed_prob_fink = [[0]]
                else:
                    transformed_prob_fink = [[0]]

                try:
                    prob_alerce = target_classification.filter(source="ALeRCE_ZTF").latest().prob_class1
                    reshaped_value = np.array([[prob_alerce]])
                    transformed_prob_alerce = model_qt_alerce.transform(reshaped_value)
                except:
                    transformed_prob_alerce = [[0]]

                try:
                    #ATAT distribution differs substantially, is used directly.
                    transformed_prob_alerce_atat = [[target_classification.filter(source="ALeRCE_ZTF").latest().prob_class4]]
                except:
                    transformed_prob_alerce_atat = [[0]]

                try:
                    prob_bogus = target_classification.filter(source="ALeRCE_ZTF").latest().prob_class3
                except:
                    prob_bogus = 0


                try:
                    pixel_index = hp.ang2pix(nside, target.ra, target.dec, lonlat=True, nest=True)                   
                    transformed_prob_nsquare = hpx_map[pixel_index] #to be included when rescaled map is available
                except:
                    transformed_prob_nsquare = 0

                transformed_prob_antares = 0            #to be included when filter is available
                try:
                    with transaction.atomic():
                        m = MicrolensingRadarData.objects.update_or_create(target=target,
                                                        metric_fink= transformed_prob_fink[0][0],
                                                        metric_alerce= transformed_prob_alerce[0][0],
                                                        metric_alerce_atat= transformed_prob_alerce_atat[0][0],
                                                        metric_antares = prob_red_chisqr_antares,
                                                        metric_nsquare = transformed_prob_nsquare,
                                                        metric_planet = transformed_prob_planet[0][0],
                                                        metric_bogus = prob_bogus,
                                                        metric_probability_ratio = prob_contrast,
                                                        average_master_probability=np.mean([transformed_prob_planet[0][0],
                                                                                            transformed_prob_nsquare,
                                                                                            transformed_prob_antares,
                                                                                            transformed_prob_alerce[0][0],
                                                                                            transformed_prob_alerce_atat[0][0],
                                                                                            prob_contrast,
                                                                                            prob_red_chisqr_antares
                                                                                            ])
                                                        )
                except:
                    print('Rescaled probabilities failed for ' + target.name)
            try:                
                with transaction.atomic():
                    filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                    pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                    filtered_target.update(expected_visits = visit_map[pixel_index])
            except:
                print('Expected visits failed for ' + target.name)
                
        print('rescaled probabilities created/updated.')
        #Filter for to ranked events and augment with variability information



