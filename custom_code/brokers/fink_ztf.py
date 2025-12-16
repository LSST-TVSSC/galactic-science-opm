from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from tom_alerts.alerts import GenericBroker, GenericQueryForm
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

class FINKQueryForm(GenericQueryForm):
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

class FINKBroker(GenericBroker):
    name = 'FINK_ZTF'
    form = FINKQueryForm

    def fetch_alerts(self, events=30):
        """Fetch data on microlensing events discovered by FINK"""
        #use api fink query to retrieve microlensing candidates
        r = requests.post(
            "https://api.fink-portal.org/api/v1/latests",
            json={
                "class": "Microlensing candidate",
                "output-format": "json",
                "output-format": "json",
                "n": str(options['target_name_contains']),
            },
        )
        #convert to pandas df
        FINK_results = pd.read_json(io.BytesIO(r.content))

        #ingest the OPM TOM db
        (list_of_targets, new_targets) = self.ingest_events(FINK_results)

        return list_of_targets, new_targets

    def ingest_events(self, FINK_results, debug=False):
        """Function to ingest the targets into the OPM database"""
        print('FINK harvester: ingesting events')

        list_of_targets = []
        new_targets = []
        if FINK_results.empty:
            return [],[]

        for event_name, event_probability,ra,dec in zip(FINK_results["i:objectId"],
                                                        FINK_results["d:mulens"],
                                                        FINK_results["i:ra"],
                                                        FINK_results["i:dec"]):

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
                    print('FINK harvester: added event '+event_name+' to OPM')
                    new_targets.append(target)

            else:
                print('FINK harvester: found ' + str(qs.count()) + ' targets with name ' + event_name)
                target = qs[0]
            #update or create the respective probability

            qs = GalacticTarget.objects.filter(name=event)
            target_list = list(set(qs))
            print('Check lc_classifier_d:mulens from FINK ' + target.name)
            time_now = Time(datetime.datetime.now()).jd
            
            #missing, average probabilities, for feature include brightness and Nsquare           
            m = Classification.objects.update_or_create(target=target,
                                                        source='FINK_ZTF',
                                                        class1='microlensing',
                                                        prob_class1 = event_probability
                                                        )
            
            
        print('probabilities created/updated.')
        list_of_targets.append(target)

        print('FINK ZTF harvester: completed ingest of events, including ' + str(len(new_targets)) + ' new targets')

        return list_of_targets, new_targets

    def find_and_ingest_photometry(self, targets):
        print('FINK harvester: ingesting photometry')

        for target in targets:
            print('FINK harvester: ingesting photometry for event ' + target.name)
            try:
                detections_photometry, forced_photometry = self.read_FINK_lightcurve(target)
                status = self.ingest_FINK_photometry(target, detections_photometry, forced_photometry)
                print('FINK harvester: completed read and ingested photometry for event ' + target.name)
            except:
                print('FINK harvester: WARNING reading photometry failed for '
                                    + target.name + ', skipping ingest')

        print('FINK harvester: Completed ingest of photometry')

    def to_generic_alert(self, alert):
        pass
  
