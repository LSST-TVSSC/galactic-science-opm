from django.core.exceptions import MultipleObjectsReturned
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django.db import transaction
from django import forms
from django.apps import apps
from custom_code.target_models import GalacticTarget
from custom_code.match_managers import validators
from tom_dataproducts.models import ReducedDatum
from astropy.coordinates import SkyCoord, Angle
from astropy.time import Time, TimezoneInfo
import astropy.units as unit
from astroquery.vizier import Vizier
from custom_code.utils.catalog_requests import get_glade_plus_count
from custom_code.utils.catalog_requests import get_var_star_variability_analysis
import healpy as hp
import pandas as pd
from alerce.core import Alerce
from antares_client.search import search


class ANTARESQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)
    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in degrees'
    )

    def clean(self):
        if len(self.cleaned_data['target_name']) == 0 and \
                        len(self.cleaned_data['cone']) == 0:
            raise forms.ValidationError(
                "Please enter either a target name or cone search parameters"
                )

class ANTARESBroker(GenericBroker):
    name = 'ANTARES'
    form = ANTARESQueryForm

    def fetch_alerts(self, days=2):
        """
        Fetches and processes microlensing alerts from the Antares broker
        tagged microlensing
        """
        print("ANTARES microlensing combi harvester: Initiate search...")
        now = Time.now()
        mjd_start = int(now.mjd - days)
        mjd_end = int(now.mjd)

        query = {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "properties.newest_alert_observation_time": {
                                "gte": mjd_start,
                                "lt": mjd_end,
                                }
                            }
                        },
                        {
                            "term": {
                                "tags": "microlensing_candidate"
                            }
                        }
                    ]
                }
            }
        }
        print(f"Searching for microlensing candidates between MJD {mjd_start} and {mjd_end}...")
        # compile results, consider to move logic to ingest events, to enable iterating over loci
        locus_results = list(search(query))
        
        if not locus_results:
            print("ANTARES: No new alerts found.")
            return [], []
        else:
            print(f"ANTARES: Found {len(locus_results)} microlensing candidates.")

        (list_of_targets, new_targets) = self.ingest_events(locus_results)

        return (
            list_of_targets, 
            new_targets
        )
    
    def ingest_events(self, locus_list, debug=False):
        """
        Function to ingest the targets from a list of ANTARES loci 
        into the OPM database. All surveys.
        """
        print('Antares harvester: ingesting events from locus objects')
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
        list_of_targets = []
        new_targets = []
        
        if not locus_list:
            return [], []

        for locus in locus_list:
            if locus.properties['survey']['lsst']['dia_object_id'] != []:
                event_name = f"LSST_{locus.properties['survey']['lsst']['dia_object_id'][0]}"
            elif locus.properties['survey']['ztf']['id'] != []:
                event_name = locus.properties['survey']['ztf']['id'][0]
            else:    
                event_name = locus.locus_id
            
            if 'tns_public_objects' in locus.catalogs:
                try:
                    catalog_data = locus.catalog_objects
                    known_aliases = catalog_data['tns_public_objects'][0]['internal_names'].split(", ")
                except Exception as e:
                    print(f"No known aliases, exception {e}")
            else:
                known_aliases=[]
            qs = GalacticTarget.objects.filter(name=event_name)
            if len(qs) == 0:
                s = SkyCoord(locus.coordinates.ra.deg, locus.coordinates.dec.deg, unit=(unit.deg, unit.deg), frame='icrs')
                target, result = validators.get_or_create_event(
                    event_name,
                    locus.coordinates.ra.deg,
                    locus.coordinates.dec.deg,
                    debug=debug
                )
                try:
                    for alias_name in known_aliases:
                        target_tmp, result_tmp = validators.get_or_create_event(
                            alias_name,
                            locus.coordinates.ra.deg,
                            locus.coordinates.dec.deg,
                        debug=debug
                    )
                except Exception as e:
                    print(f"Creating alias: {e}")

                if result == 'new_target':
                    print('ANTARES microlensing filter harvester: added event '+event_name+' to OPM')
                    new_targets.append(target)
                    filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                    with transaction.atomic():
                        filtered_target.update(permissions = GalacticTarget.Permissions.PUBLIC)
                    try:
                        result = get_glade_plus_count(s)
                        with transaction.atomic():
                            pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                            filtered_target.update(expected_visits = visit_map[pixel_index])
                            if result > 0:
                                filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.IN_GLADE_PLUS)
                            elif result == 0:
                                filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS)
                    except:
                        print('Expected visits or GLADE+ check failed for ' + target.name)

                    try:
                        if "ZTF" in target.name or "LSST_" in target.name:
                           result_var_vizier=get_var_star_variability_analysis(target.ra, target.dec)
                        if result_var_vizier!="" and result_var_vizier!=None:
                            filtered_target.update(known_variability = result_var_vizier)
                        else:
                            filtered_target.update(known_variability = "None, queried")
                    except:
                        print('Vizier query failed for ' + target.name)


            else:
                print('ANTARES microlensing filter: found ' + str(qs.count()) + ' targets with name ' + event_name)
                target = qs[0]


            list_of_targets.append(target)

        print('ANTARES microlensing filter: completed ingest of events, including ' + str(len(new_targets)) + ' new targets')

        return list_of_targets, new_targets

    def find_and_ingest_photometry(self, targets):
        print('ANTARES microlensing filter: ingesting photometry')
        targets_ztf = [x for x in targets if 'ZTF' in "".join(x.names)]
        for target in targets_ztf:
            print('ANTARES microlensing filter with ZTF ALERCE harvester: ingesting photometry for event ' + target.name)
            try:
                detections_photometry, forced_photometry = self.read_ALERCE_lightcurve(target)
                status = self.ingest_ALERCE_photometry(target, detections_photometry, forced_photometry)
                print('ANTARES microlensing filter harvester: completed read and ingested photometry for event ' + target.name)
            except Exception as e:
                print('ANTARES microlensing filter harvester: WARNING reading photometry failed for '
                                    + target.name + ', skipping ingest ',e)

        print('ANTARES microlensing filter harvester: Completed ingest of photometry')

    def read_ALERCE_lightcurve(self, target, survey = 'ztf'):
        """Method to read the ALERCE lightcurve via alerce api client"""
        from alerce.core import Alerce
        alerce = Alerce()
        photometry = []
        target_name_ztf = [x for x in target.names if "ZTF" in x][0]
        ALERCE_name = target_name_ztf
        detections_photometry = alerce.query_detections(ALERCE_name,
                                     format="pandas", survey = survey)
        #remove multiple detections
        detections_photometry = detections_photometry.drop_duplicates(subset="mjd")
        forced_photometry = alerce.query_forced_photometry(ALERCE_name,
                                     format="pandas", survey = survey)

        return detections_photometry, forced_photometry

    def ingest_ALERCE_photometry(self, target, detections_photometry, forced_photometry, survey = 'ztf', debug=False):
        """Method to store the photometry datapoints in the OPM TOM as ReducedDatums"""
        filter_definition = {1:"ZTF_g", 2:"ZTF_r", 3:"ZTF_i"}
        for i, row in detections_photometry.iterrows():
            jd = Time(row["mjd"], format='mjd', scale='utc')
            jd.to_datetime(timezone=TimezoneInfo())
            if "magpsf_corr" in detections_photometry.columns :
                if not pd.isna(row["magpsf_corr"]) and row["magpsf_corr"]<100.:
                    datum = {'magnitude': row["magpsf_corr"],
                            'filter': filter_definition[row["fid"]],
                            'error': row["sigmapsf_corr_ext"]
                            }          
                    try:
                        with transaction.atomic():
                            rd, created = ReducedDatum.objects.update_or_create(
                                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                value=datum,
                                source_name='ALERCE',
                                source_location=target.name,
                                data_type='photometry',
                                target=target)

                    except MultipleObjectsReturned:
                        print('ALERCE HARVESTER: Found duplicated data for event '+target.name)
        if "mag_corr" in forced_photometry.columns and "mjd" in forced_photometry.columns:
            for i, row in forced_photometry.iterrows():

                jd = Time(row["mjd"], format='mjd', scale='utc')
                jd.to_datetime(timezone=TimezoneInfo())
                if not pd.isna(row["mag_corr"]) and row["mag_corr"]<100.:
                    datum = {'magnitude': row["mag_corr"],
                            'filter': filter_definition[row["fid"]],
                            'error': row["e_mag_corr_ext"]
                            }
                    try:
                        with transaction.atomic():
                            rd, created = ReducedDatum.objects.update_or_create(
                                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                value=datum,
                                source_name='ALERCE',
                                source_location=target.name,
                                data_type='photometry',
                                target=target)

                    except MultipleObjectsReturned:
                        print('ALERCE HARVESTER: Found duplicated data for event '+target.name)
                

        return 'OK'


    def to_generic_alert(self, alert):
        pass
  
