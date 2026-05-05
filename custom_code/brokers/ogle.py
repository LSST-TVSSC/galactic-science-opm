from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django.db import transaction
from django import forms
from django.apps import apps
from django.db.utils import IntegrityError
from custom_code.target_models import GalacticTarget, MicrolensingModel, Classification
from custom_code.match_managers import validators
from tom_observations import facility
from tom_dataproducts.models import ReducedDatum
from astropy.coordinates import SkyCoord, Galactic, Angle
from astropy.time import Time, TimezoneInfo
import astropy.units as unit
from astroquery.vizier import Vizier
import healpy as hp
import os
import numpy as np
import requests

BROKER_URL = 'https://www.astrouw.edu.pl/ogle/ogle4/ews'

class OGLEQueryForm(GenericQueryForm):
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

class OGLEBroker(GenericBroker):
    name = 'OGLE'
    form = OGLEQueryForm

    def fetch_alerts(self, years = [], events='all'):
        """Fetch data on microlensing events discovered by OGLE"""

        # Read the lists of events for the given years
        ogle_events = self.fetch_lens_model_parameters(years)

        # Apply selection of events, if any
        if str(events).lower() != 'all' and not str(events).isnumeric():
            event_selection = {}
            event_selection[events] = ogle_events[events]
        else:
            event_selection = ogle_events

        #ingest the OPM TOM db
        (list_of_targets, new_targets) = self.ingest_events(event_selection)

        return list_of_targets, new_targets

    def fetch_lens_model_parameters(self, years):
        """Method to retrieve the text file of the model parameters for fits by the OGLE survey"""
        print('OGLE harvester: Fetching event model parameters for years '+repr(years))

        events = {}
        for year in years:
            par_file_url = os.path.join(BROKER_URL,year,'lenses.par')
            response = requests.request('GET', par_file_url)
            print('OGLE harvester: retrieving parameters for events from '
                            +str(year)+' with status '+str(response.status_code))
            if response.status_code == 200:
                for line in response.iter_lines():
                    line = str(line)
                    if 'StarNo' not in line and len(line) > 5:      # Skip the file header
                        entries = line.split()
                        name = 'OGLE-'+entries[0].replace("b'","")
                        ra = entries[3]
                        dec = entries[4]
                        events[name] = (ra,dec)

        print('OGLE harvester: found ' + str(len(events)) + ' event(s)')

        return events

    def ingest_events(self, ogle_events, debug=False):
        """Function to ingest the targets into the OPM database"""
        print('OGLE harvester: ingesting events')
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
        list_of_targets = []
        new_targets = []

        for event_name, event_params in ogle_events.items():

            qs = GalacticTarget.objects.filter(name=event_name)

            if len(qs) == 0:
                s = SkyCoord(event_params[0], event_params[1], unit=(unit.hourangle, unit.deg), frame='icrs')
                target, result = validators.get_or_create_event(
                    event_name,
                    s.ra.deg,
                    s.dec.deg,
                    debug=debug
                )

                if result == 'new_target':
                    print('OGLE harvester: added event '+event_name+' to OPM')
                    new_targets.append(target)
                    filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                    filtered_target.update(permissions = GalacticTarget.Permissions.PUBLIC)
                    try:
                        with transaction.atomic():
                            filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                            pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                            filtered_target.update(expected_visits = visit_map[pixel_index])
                    except:
                        print('Expected visits or GLADE+ check failed for ' + target.name)


            else:
                print('OGLE harvester: found ' + str(qs.count()) + ' targets with name ' + event_name)
                target = qs[0]

            list_of_targets.append(target)

        print('OGLE harvester: completed ingest of events, including ' + str(len(new_targets)) + ' new targets')

        return list_of_targets, new_targets

    def find_and_ingest_photometry(self, targets, full_phot=False):
        current_year = str(int(Time.now().byear))
        previous_year = str(int(Time.now().byear)-1)
        print('OGLE harvester: ingesting photometry')

        for target in targets:
            print('OGLE harvester: ingesting photometry for event ' + target.name)
            try:
                year = target.name.split('-')[1]
                event = target.name.split('-')[2]+'-'+target.name.split('-')[3]

                # harvest the photometry for all years
                if int(year) > 1990:
                    try:
                        photometry = self.read_ogle_lightcurve(target)
                        status = self.ingest_ogle_photometry(target, photometry)
                        print('OGLE harvester: completed read and ingested photometry for event ' + target.name)
                    except IndexError:
                        print('OGLE harvester: WARNING malformed photometry for event '
                                    + target.name + ', skipping ingest')

            except IndexError:
                print('OGLE harvester: Encountered malformed target name ' + target.name + ', skipped ingest')

        print('OGLE harvester: Completed ingest of photometry')

    def read_ogle_lightcurve(self, target):
        """Method to read the OGLE lightcurve via HTTP"""
        photometry = []
        ogle_name = target.__repr__()
        if 'OGLE' in ogle_name:
            year = ogle_name.split('-')[1]
            event = ogle_name.split('-')[2] + '-' + ogle_name.split('-')[3]

            lc_file_url = os.path.join(BROKER_URL, year, event.lower()[:-1], 'phot.dat')
            response = requests.request('GET', lc_file_url)
            if response.status_code == 200:
                for line in response.iter_lines():
                    entries = str(line).replace('\n','').replace("b'",'').replace("'",'').split()
                    photometry.append( [float(x) for x in entries] )
            print('OGLE harvester: read and ingested photometry for event ' + target.name
                        + ' from file ' + os.path.join(event.lower(), 'phot.dat'))

        else:
            print('OGLE Harvester WARNING: No OGLE name available for target '
                        + target.name + ' so cannot find lightcurve to ingest')

        return np.array(photometry)

    def ingest_ogle_photometry(self, target, photometry):
        """Method to store the photometry datapoints in the OPM TOM as ReducedDatums"""

        for i in range(0,len(photometry),1):
            jd = Time(photometry[i][0], format='jd', scale='utc')
            jd.to_datetime(timezone=TimezoneInfo())
            datum = {'magnitude': photometry[i][1],
                    'filter': 'OGLE_I',
                    'error': photometry[i][2]
                    }
            try:
                with transaction.atomic():
                    rd, created = ReducedDatum.objects.get_or_create(
                        timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                        value=datum,
                        source_name='OGLE',
                        source_location=target.name,
                        data_type='photometry',
                        target=target)

            except MultipleObjectsReturned:
                print('OGLE HARVESTER: Found duplicated data for event '+target.name)

        target.save()

        return 'OK'

    def sort_target_list(self, list_of_targets):
        name_list = np.array([x.name for x in list_of_targets])
        order = np.argsort(name_list)
        order = order[::-1]
        return (np.array(list_of_targets)[order]).tolist()

    def select_random_targets(self, list_of_targets, new_targets, ntargets=100):
        target_index = np.random.randint(0,len(list_of_targets)-1, size=ntargets)

        # Numpy's random routines don't provide a sample with no unique entries,
        # so filter for that and fill in the gaps.
        target_index = np.unique(target_index)

        max_iter = 10
        i = 0
        while(len(target_index) < ntargets) and (i <= max_iter):
            i += 1
            idx = np.random.randint(0,len(list_of_targets), size=1)[0]
            if idx not in target_index:
                target_index = np.append(target_index, idx)

        random_targets = (np.array(list_of_targets)[target_index]).tolist()

        # If a subset of events has been requested, priorities the new targets first, up to the maximum number allowed
        event_list = []
        i = 0
        while (len(event_list) < ntargets) and (i < len(new_targets)):
            event_list.append(new_targets[i])
            i += 1

        # If there is any space left, add existing events to the selection
        i = 0
        if len(event_list) < ntargets:
            while (len(event_list) < ntargets) and (i < len(random_targets)):
                event_list.append(random_targets[i])
                i += 1

        return np.array(event_list)

    def to_generic_alert(self, alert):
        pass
  
