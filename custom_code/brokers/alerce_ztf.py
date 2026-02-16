from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django.db import transaction
from django import forms
from django.db.utils import IntegrityError
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from tom_observations import facility
from tom_dataproducts.models import ReducedDatum
from astropy.coordinates import SkyCoord, Galactic
from astropy.time import Time, TimezoneInfo
import astropy.units as unit
import os
import numpy as np
import requests
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

    def fetch_alerts(self, events=10,days=10,survey = 'ztf'):
        """Fetch data on microlensing events discovered by ALERCE"""
        from alerce.core import Alerce
        alerce = Alerce()
        # Query the list of microlensing events, last 10d, 10 events page1
        # 
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

        #ingest the OPM TOM db and restart CV query
        (list_of_targets, new_targets) = self.ingest_events(alerce_results)
        alerce_results = alerce.query_objects(
            classifier="lc_classifier_BHRF_forced_phot",
            class_name="CV/Nova",
            format="pandas",
            firstmjd=float(int(Time.now().mjd)-days),
            page_size=events,
            order_by="probability",
            order_mode="DESC",
            survey = survey
        )    
        (list_of_targets, new_targets) = self.ingest_events(alerce_results)

        return list_of_targets, new_targets

    def ingest_events(self, alerce_results, survey = 'ztf', debug=False):
        """Function to ingest the targets into the OPM database"""
        print('ALERCE harvester: ingesting events')

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

    def read_ALERCE_lightcurve(self, target, survey = 'ztf'):
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

    def ingest_ALERCE_photometry(self, target, detections_photometry, forced_photometry, survey = 'ztf', debug=False):
        """Method to store the photometry datapoints in the OPM TOM as ReducedDatums"""
        filter_definition = {1:"ZTF_g", 2:"ZTF_r", 3:"ZTF_i"}
        for i, row in detections_photometry.iterrows():
            jd = Time(row["mjd"], format='mjd', scale='utc')
            jd.to_datetime(timezone=TimezoneInfo())
            datum = {'magnitude': row["magpsf_corr"],
                    'filter': filter_definition[row["fid"]],
                    'error': row["sigmapsf_corr_ext"]
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
                with transaction.atomic():
                    rd, created = ReducedDatum.objects.get_or_create(
                        timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                        value=datum,
                        source_name='ALERCE',
                        source_location=target.name,
                        data_type='photometry',
                        target=target)

            except MultipleObjectsReturned:
                print('ALERCE HARVESTER: Found duplicated data for event '+target.name)


        target.save()

        return 'OK'


    def to_generic_alert(self, alert):
        pass
  
