import os
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import TargetExtra
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from astropy.time import Time, TimeDelta
from custom_code.target_models import GalacticTarget, MicrolensingModel, MicrolensingRadarData, MicrolensingStatisticalModel, StatisticalModelImage
from custom_code.utils.catalog_requests import query_ztf_lightcurve
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation
import RTModel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import RTModel.plotmodel as plm
import astropy.units as u
from astropy.time import Time, TimezoneInfo
import pandas as pd
import tempfile
from os import path
from os import makedirs, listdir
from django.db import connection, transaction
from ._RTModel_results_cls import EventResults, ModelResults
import sys


def run_fit(target):
    if "ZTF" in target.name or "LSST" in target.name or "OGLE" in target.name:
        target_id = target.id 
        tempdirname = 'event001'
        print(f"Prepare RTModel fit for {target.name}")
        with tempfile.TemporaryDirectory() as tempdirname:      
            data_dir = path.join(tempdirname,'Data')
            makedirs(data_dir)
            input_path = path.join(tempdirname, 'input_data.csv')
            model_output = path.join(tempdirname, 'model_results.pkl')
            #RTModel.fit(input_path, output=model_output)
            with transaction.atomic():
                photometry = ReducedDatum.objects.filter(data_type='photometry', target=target).order_by('-timestamp')
                data = []
                #required format # Mag err HJD-2450000
                target_coord = SkyCoord(ra = target.ra, dec = target.dec, unit='deg', frame='icrs')
                # RTM requires a sexagesimal string (HH:MM:SS.S DD:MM:SS.S)
                with open(path.join(data_dir,"event001.coordinates"),'w') as fp:
                    fp.write(target_coord.to_string('hmsdms',sep=':'))
                
                if "ZTF" in str(target.name):
                    location = EarthLocation.from_geodetic(lon=-116.859722 * u.deg, lat=33.357222 * u.deg,
                                                           height=1700 * u.m)   
                else:
                    #default location for all other data, Rubin
                    location = EarthLocation.from_geodetic( lat='-30d14m40.68s', lon='-70d44m57.90s', height=2647.*u.m)
                for reduced_datum in photometry:
                    t = Time(reduced_datum.timestamp, scale='utc')
                    ltt_heliocentric = t.light_travel_time(target_coord, kind='heliocentric', location=location)
                    hjd_values_rtm = t.jd + ltt_heliocentric.value -2450000.
                    try:
                        current_time = Time.now()
                        age = current_time - t
                        #TBD revise with filter
                        if age < TimeDelta(10*365., format='jd'): 
                            rd_data = {'timestamp': hjd_values_rtm }
                            rd_data['magnitude'] = reduced_datum.value['magnitude']
                            rd_data['error'] = reduced_datum.value['error']
                            rd_data['filter'] = reduced_datum.value['filter']
                            data.append(rd_data)
                    except:
                        print("No photometry with suitable mags for RTModel")
                df = pd.DataFrame.from_dict(data)
                if 'filter' in df.columns:
                    unique_categories = df['filter'].unique()
                    for category in unique_categories:
                        filtered_df = df[df['filter'] == category]
                        if len(filtered_df)>2:
                            custom_header = ["Mag", "err", "HJD-2450000"]
                            try:
                                filtered_df.to_csv(path.join(data_dir,f"{category}.dat"), columns= ['magnitude','error','timestamp'], 
                                      header=custom_header, index=None, sep=' ', mode='a')
                            except Exception as e:
                                print(f"Cannot write filtered dataframe {e}")
                    rtm = RTModel.RTModel(tempdirname)
                    rtm.config_InitCond(modelcategories = ['PS'])
                if len(data)>3:
                    rho_constraints = [['log_rho', -3., -10., 0.01],['log_tE', 1.6, -0.5, 0.5]]
                    rtm.set_constraints(rho_constraints)
                    rtm.run()
                    event_path = path.join(tempdirname)
                    saving_path =path.join(settings.MEDIA_ROOT, f"{target.name}.png")  
                    try:                   
                        model_name = listdir(path.join(tempdirname,"FinalModels"))
                        model_path = path.join(tempdirname,"FinalModels",model_name[0])
                        model_results = ModelResults(model_path)
                        if (model_results.model_parameters.u0_error+model_results.model_parameters.u0 < 5. and \
                           model_results.model_parameters.tE > 0. and \
                           model_results.model_parameters.u0_error > 0.) or "LSST" in target.name :
                            plm.plotmodel(eventname=event_path, modelfile=model_path)
                            plt.savefig(saving_path, bbox_inches='tight',dpi=90)
                            plt.close()
                        with transaction.atomic():
                            ml_model = MicrolensingStatisticalModel.objects.create(
                                target=target,
                                u0=model_results.model_parameters.u0,
                                t0=model_results.model_parameters.t0,
                                tE=model_results.model_parameters.tE,
                                err_u0=model_results.model_parameters.u0_error,
                                err_t0=model_results.model_parameters.t0_error,
                                err_tE=model_results.model_parameters.tE_error,
                                err_rho=model_results.model_parameters.rho_error,
                                rho=model_results.model_parameters.rho,
                            )
                            image_path = Path(saving_path)
                            with image_path.open(mode="rb") as f:
                                image = File(f, name=image_path.name)
                                StatisticalModelImage.objects.create(
                                    statistical_model=ml_model, image=image
                                )
                                os.remove(saving_path)


                    except Exception as e:
                        print("No FinalModel from RTModel")
                        print(e)


class Command(BaseCommand):
    help = 'Fit events with PSPL and parallax, then ingest fit parameters in MicrolensingModel'

    def add_arguments(self, parser):
        parser.add_argument('event', help='Eventname')

    def handle(self, *args, **options):
        if str(options['event']) != "ZTF" and str(options['event']) != "LSST" :
            qs=GalacticTarget.objects.filter(name__icontains=str(options['event']))
            for target in qs:
                run_fit(target)
        else:            
            #Check for updated events (last 3 days)
            #Check for top 35 priority events
            #Combine check and run fit
            time_window = timezone.now() - timedelta(days=3)
            new_or_modified_targets = GalacticTarget.objects.filter(
            Q(modified__gte=time_window) | 
            Q(reduceddatum__timestamp__gte=time_window)).filter(
            name__icontains=str(options['event'])).filter(
            known_variability__icontains="queried").distinct()
            distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(
            target__name__icontains=str(options['event'])).filter(
            average_master_probability__gt=0.).filter(
            target__known_variability__icontains="queried")
            if str(options['event']) == "LSST":
                qs = MicrolensingRadarData.objects.filter(target__name__icontains=str(options['event'])).distinct()
            else:
                qs = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').distinct()[:35]
            # extract target names, avoid duplicates via set
            target_names = list(set([x.target.name for x in qs] + [x.name for x in new_or_modified_targets ] ))
            for target_name in target_names:
                target = GalacticTarget.objects.filter(name__icontains=target_name).last()
                if not target.ztf_baseline_checked:
                    baseline_photometry_r = query_ztf_lightcurve(target.ra,target.dec,2.,start_mjd=58500.0, passband="r")
                    baseline_photometry_g = query_ztf_lightcurve(target.ra,target.dec,2.,start_mjd=58500.0, passband="g")
                    baseline_photometry_i = query_ztf_lightcurve(target.ra,target.dec,2.,start_mjd=58500.0, passband="i")
                    baseline_photometry = pd.concat([baseline_photometry_r,
                                                     baseline_photometry_g,
                                                     baseline_photometry_i], ignore_index=True)
                    target.ztf_baseline_checked = True
                    target.save(update_fields=['ztf_baseline_checked'])
                    filter_definition = {"zg":"ZTF_g", "zr":"ZTF_r", "zi":"ZTF_i"}
                    if "mag" in baseline_photometry.columns and "mjd" in baseline_photometry.columns:
                        for i, row in baseline_photometry.iterrows():
                            jd = Time(row["mjd"], format='mjd', scale='utc')
                            jd.to_datetime(timezone=TimezoneInfo())
                            if "mag" in baseline_photometry.columns :
                                if not pd.isna(row["mag"]) and row["mag"]<100.:
                                    datum = {'magnitude': row["mag"],
                                            'filter': filter_definition[row["filtercode"]],
                                            'error': row["magerr"]
                                            }
                            try:
                                with transaction.atomic():
                                    rd, created = ReducedDatum.objects.get_or_create(
                                        timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                        value=datum,
                                        source_name='ALERCE',
                                        source_location=target.name,
                                        data_type='photometry',
                                        target=target)
                            except Exception as e:
                                print(f'Unexpected exception {e}')
                run_fit(target)
        
                
