from django.core.management.base import BaseCommand
from tom_dataproducts.models import PhotometryReducedDatum, ReducedDatum
from tom_targets.models import Target
from django.conf import settings
from django.db import transaction
from astropy.time import Time
from custom_code.target_models import GalacticTarget, MicrolensingModel
from custom_code.utils.catalog_requests import query_ztf_lightcurve
from astropy.time import Time, TimezoneInfo
from astropy.coordinates import SkyCoord, EarthLocation
import RTModel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import RTModel.plotmodel as plm
import astropy.units as u
import pandas as pd
import tempfile
from os import path
from os import makedirs, listdir
import numpy as np
from django.db import connection, transaction
from ._RTModel_results_cls import EventResults, ModelResults

def run_fit(target):
    target_id = target.id 
    tempdirname = 'event001'
    print(target.name)

    with tempfile.TemporaryDirectory() as tempdirname:      
        data_dir = path.join(tempdirname,'Data')
        makedirs(data_dir)
        input_path = path.join(tempdirname, 'input_data.csv')
        model_output = path.join(tempdirname, 'model_results.pkl')
        #RTModel.fit(input_path, output=model_output)
        with transaction.atomic():
            photometry = PhotometryReducedDatum.objects.filter(target=target).order_by('-timestamp')
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
                    rd_data = {'timestamp': hjd_values_rtm }
                    rd_data['magnitude'] = reduced_datum.brightness
                    rd_data['error'] = reduced_datum.brightness_error
                    rd_data['filter'] = reduced_datum.bandpass
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
                        filtered_df.to_csv(path.join(data_dir,f"{category}.dat"), columns= ['magnitude','error','timestamp'], 
                                  header=custom_header, index=None, sep=' ', mode='a')
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
                    plm.plotmodel(eventname=event_path, modelfile=model_path)
                    plt.savefig(saving_path, bbox_inches='tight',dpi=90)
                    with transaction.atomic():
                        m = MicrolensingModel.objects.update_or_create(target=target,
                                              u0 = model_results.model_parameters.u0,
                                              t0 = model_results.model_parameters.t0,
                                              tE = model_results.model_parameters.tE,
                                              err_u0 = model_results.model_parameters.u0_error,
                                              err_t0 = model_results.model_parameters.t0_error,
                                              err_tE = model_results.model_parameters.tE_error,
                                              err_rho = model_results.model_parameters.rho_error, 
                                              rho = model_results.model_parameters.rho)
                except :
                    print("No FinalModel from RTModel")


class Command(BaseCommand):
    help = 'Fit events with PSPL and parallax, then ingest fit parameters in MicrolensingModel'

    def add_arguments(self, parser):
        parser.add_argument('event', help='Eventname')

    def handle(self, *args, **options):
        qs = GalacticTarget.objects.filter(name__icontains=str(options['event']))
        if len(qs)>0:
            target = Target.objects.get(name=str(options['event']))
            if not target.ztf_baseline_checked:
                baseline_photometry_r = query_ztf_lightcurve(target.ra,target.dec,2.,start_mjd=58500.0, passband="r")
                baseline_photometry_g = query_ztf_lightcurve(target.ra,target.dec,2.,start_mjd=58500.0, passband="g")
                baseline_photometry = pd.concat([baseline_photometry_r,baseline_photometry_g], ignore_index=True)
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
                                rd, created = PhotometryReducedDatum.objects.get_or_create(
                                    timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                    brightness = datum["magnitude"],
                                    brightness_error = datum["error"],
                                    bandpass = datum["filter"],
                                    source_name='ALERCE',
                                    source_location=target.name,
                                    target=target)
                        except Exception as e:
                            print(f'Unexpected exception {e}')
            
            run_fit(target)

                
