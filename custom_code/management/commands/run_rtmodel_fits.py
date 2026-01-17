from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
from django.conf import settings
from django.db import transaction
from astropy.time import Time
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
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
import datetime
from os import path
from os import makedirs, listdir
import numpy as np
from django.db import connection
from ._RTModel_results_cls import EventResults, ModelResults

def run_fit(target):
    if "ZTF26" in target.name or "LSST" in target.name or "OGLE" in target.name:
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
                            filtered_df.to_csv(path.join(data_dir,f"{category}.dat"), columns= ['magnitude','error','timestamp'], 
                                      header=None, index=None, sep=' ', mode='a')
                    rtm = RTModel.RTModel(tempdirname)
                    rtm.config_InitCond(modelcategories = ['PS'])
                if len(data)>3:
                    rtm.run()
                    event_path = path.join(tempdirname)
                    saving_path =path.join(settings.MEDIA_ROOT, f"{target.name}.png")  
                    try:                   
                        model_name = listdir(path.join(tempdirname,"FinalModels"))
                        model_path = path.join(tempdirname,"FinalModels",model_name[0])
                        model_results = ModelResults(model_path)
                        if model_results.model_parameters.u0_error+model_results.model_parameters.u0 < 3.:
                            plm.plotmodel(eventname=event_path, modelfile=model_path)
                            plt.savefig(saving_path, bbox_inches='tight',dpi=90)

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
        if str(options['event']) != "all":
            qs = GalacticTarget.objects.filter(name__icontains=str(options['event']))
            if len(qs)>0:
                target = Target.objects.get(name=str(options['event']))
                run_fit(target)
        else:
            qs = GalacticTarget.objects.filter(name__icontains="ZTF")
            target_list = list(set(qs))
            for target in target_list:
                run_fit(target)
                
            qs = GalacticTarget.objects.filter(name__icontains="LSST")
            target_list = list(set(qs))
            for target in target_list:
                run_fit(target)
                