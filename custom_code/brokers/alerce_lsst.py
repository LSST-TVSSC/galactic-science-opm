from django.core.exceptions import MultipleObjectsReturned
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django import forms
from django.apps import apps
from django.db import transaction
from custom_code.target_models import GalacticTarget
from custom_code.match_managers import validators
from tom_dataproducts.models import PhotometryReducedDatum, ReducedDatum
from astropy.coordinates import SkyCoord, Angle
from astropy.time import Time, TimezoneInfo
import astropy.units as unit
from astroquery.vizier import Vizier
from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG, get_glade_plus_count
from custom_code.utils.catalog_requests import get_var_star_variability_analysis
import healpy as hp
from alerce.core import Alerce

class ALERCEQueryForm(GenericQueryForm):
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

class ALERCEBroker(GenericBroker):
    name = 'ALERCE'
    form = ALERCEQueryForm

    def fetch_alerts(self, events=5,days=5,survey = 'lsst'):
        """Fetch data on microlensing events discovered by ALERCE"""
        from alerce.core import Alerce
        alerce = Alerce()
        # Query the list of microlensing events, last 10d, 10 events page1
        alerce_results = alerce.query_objects(
            classifier="lc_classifier_BHRF_forced_phot",
            class_name="Microlensing",
            format="pandas",
            firstmjd=float(int(Time.now().mjd)-days),
            page_size=events,
            order_by="probability",
            order_mode="DESC",
            survey = survey
        )

        #ingest the OPM TOM db
        (list_of_targets, new_targets) = self.ingest_events(alerce_results)

        return list_of_targets, new_targets

    def ingest_events(self, alerce_results, survey = 'lsst', debug=False):
        """Function to ingest the targets into the OPM database"""
        print('ALERCE harvester: ingesting events')
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
        list_of_targets = []
        new_targets = []
        if alerce_results.empty:
            return [],[]

        for event_name, event_probability,ra,dec in zip(alerce_results["oid"],
                                                        alerce_results["probability"],
                                                        alerce_results["meanra"],
                                                        alerce_results["meandec"]):

            qs = GalacticTarget.objects.filter(name=event_name)

            if len(qs) == 0:
                s = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame='icrs')
                target, result = validators.get_or_create_event(
                    event_name,
                    s.ra.deg,
                    s.dec.deg,
                    debug=debug
                )

                if result == 'new_target':
                    print('ALERCE harvester: added event '+event_name+' to OPM')
                    new_targets.append(target)
                    filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                    filtered_target.update(permissions = GalacticTarget.Permissions.PUBLIC)
                    try:
                        result = get_glade_plus_count(s)
                        with transaction.atomic():
                            filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                            pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                            filtered_target.update(expected_visits = visit_map[pixel_index])
                            if result > 0:
                                filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.IN_GLADE_PLUS)
                            elif result==0:
                                filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS)
                    except:
                        print('Expected visits failed for ' + target.name)
                    
                    try:
                        if "ZTF" in target.name or "LSST_" in target.name:
                           result_var_vizier=get_var_star_variability_analysis(target.ra, target.dec)
                        if result_var_vizier!="" and result_var_vizier!=None:
                            filtered_target.update(known_variability = result_var_vizier)
                        else:
                            filtered_target.update(known_variability = NOT_IN_ANY_CATALOG)
                    except:
                        print('Vizier query failed for ' + target.name)
            else:
                print('ALERCE harvester: found ' + str(qs.count()) + ' targets with name ' + event_name)
                target = qs[0]

            list_of_targets.append(target)

        print('ALERCE harvester: completed ingest of events, including ' + str(len(new_targets)) + ' new targets')

        return list_of_targets, new_targets

    def find_and_ingest_photometry(self, targets):
        print('ALERCE harvester: ingesting photometry')

        for target in targets:
            print('ALERCE harvester: ingesting photometry for event ' + target.name)
            try:
                detections_photometry, forced_photometry = self.read_ALERCE_lightcurve(target)
                status = self.ingest_ALERCE_photometry(target, detections_photometry, forced_photometry)
                print('ALERCE harvester: completed read and ingested photometry for event ' + target.name)
            except:
                print('ALERCE harvester: WARNING reading photometry failed for '
                                    + target.name + ', skipping ingest')

        print('ALERCE harvester: Completed ingest of photometry')

    def read_ALERCE_lightcurve(self, target, survey = 'lsst'):
        """Method to read the ALERCE lightcurve via alerce api client"""
        from alerce.core import Alerce
        alerce = Alerce()
        photometry = []
        ALERCE_name = target.name
        detections_photometry = alerce.query_detections(ALERCE_name,
                                     format="pandas", survey = survey)
        #remove multiple detections
        detections_photometry = detections_photometry.drop_duplicates(subset="mjd")
        forced_photometry = alerce.query_forced_photometry(ALERCE_name,
                                     format="pandas", survey = survey)
        return detections_photometry, forced_photometry

    def ingest_ALERCE_photometry(self, target, detections_photometry, forced_photometry, survey = 'lsst', debug=False):
        """Method to store the photometry datapoints in the OPM TOM as ReducedDatums"""
        filter_definition = {1:"LSST_g", 2:"LSST_r", 3:"LSST_i"}
        for i, row in detections_photometry.iterrows():
            jd = Time(row["mjd"], format='mjd', scale='utc')
            jd.to_datetime(timezone=TimezoneInfo())
            datum = {'magnitude': row["magpsf_corr"],
                    'filter': filter_definition[row["fid"]],
                    'error': row["sigmapsf_corr_ext"]
                    }
            try:
                rd, created = PhotometryReducedDatum.objects.update_or_create(
                    timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                    brightness = datum["magnitude"],
                    brightness_error = datum["error"],
                    bandpass = datum["filter"],
                    source_name='ALERCE_LSST',
                    source_location=target.name,
                    target=target)

            except MultipleObjectsReturned:
                print('ALERCE HARVESTER: Found duplicated data for event '+target.name)

        for i, row in forced_photometry.iterrows():

            jd = Time(row["mjd"], format='mjd', scale='utc')
            jd.to_datetime(timezone=TimezoneInfo())
            datum = {'magnitude': row["mag_corr"],
                    'filter': filter_definition[row["fid"]],
                    'error': row["e_mag_corr_ext"]
                    }
            try:
                rd, created = PhotometryReducedDatum.objects.get_or_create(
                    timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                    brightness = datum["magnitude"],
                    brightness_error = datum["error"],
                    bandpass = datum["filter"],
                    source_name='ALERCE_LSST',
                    source_location=target.name,
                    target=target)

            except MultipleObjectsReturned:
                print('ALERCE HARVESTER: Found duplicated data for event '+target.name)


        return 'OK'


    def to_generic_alert(self, alert):
        pass
  
