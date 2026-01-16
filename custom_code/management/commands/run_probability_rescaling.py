from django.core.management.base import BaseCommand
from django.apps import apps
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification, MicrolensingRadarData
from sklearn.preprocessing import QuantileTransformer
from custom_code.match_managers import validators
import numpy as np
import pandas as pd
import datetime
from alerce.core import Alerce
from astropy.time import Time, TimezoneInfo
from astropy.coordinates import SkyCoord
from astropy import units as u
import healpy as hp
from ._rescale_ztf_microlensing_prob import psi_planet_priority_peak
import joblib

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
        hpx_map = config.nsquare_map
        nside  = config.nside

        for target in target_list:
            microlensing_model = MicrolensingModel.objects.filter(target=target).latest()

            print('Check and rescale probabilities for' + target.name)
            target_classification = Classification.objects.filter(target=target)
            if target_classification.exists():
                time_now = Time(datetime.datetime.now()).jd
                try:
                    psip = psi_planet_priority_peak(microlensing_model.u0, microlensing_model.err_u0)
                    reshaped_value = np.array([[psip]])
                    transformed_prob_planet = model_qt_psi.transform(reshaped_value)
                except:
                    transformed_prob_planet = [[0]]
                try:
                    prob_fink = 0.
                    reshaped_value = np.array([[prob_fink]])
                    transformed_prob_fink = model_qt_fink.transform(reshaped_value)
                except:
                    transformed_prob_fink = [[0]]

                try:
                    prob_alerce = 0.
                    reshaped_value = np.array([[prob_alerce]])
                    transformed_prob_alerce = model_qt_alerce.transform(reshaped_value)
                except:
                    transformed_prob_alerce = [[0]]

                try:
                    pixel_index = hp.ang2pix(nside, target.ra, target.dec, lonlat=True, nest=True)                   
                    transformed_prob_nsquare = hpx_map[pixel_index] #to be included when rescaled map is available
                except:
                    transformed_prob_nsquare = 0

                transformed_prob_antares = 0            #to be included when filter is available

            m = MicrolensingRadarData.objects.update_or_create(target=target,
                                              metric_fink= transformed_prob_fink,
                                              metric_alerce= transformed_prob_alerce,
                                              metric_antares= transformed_prob_antares,
                                              metric_nsquare = transformed_prob_nsquare,
                                              metric_planet = transformed_prob_planet,
                                              average_master_probability=np.mean([transformed_prob_planet[0][0],
                                                                                  transformed_prob_nsquare,
                                                                                  transformed_prob_antares,
                                                                                  transformed_prob_alerce[0][0]])
                                              )
            
        print('rescaled probabilities created/updated.')
