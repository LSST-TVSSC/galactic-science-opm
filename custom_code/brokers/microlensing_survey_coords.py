from django.apps import apps
from django.db import transaction
from astropy.coordinates import SkyCoord
from astropy.time import Time
import astropy.units as unit
from astroquery.vizier import Vizier
import healpy as hp
import os
import requests

from custom_code.target_models import GalacticTarget
from custom_code.match_managers import validators

OGLE_URL = 'https://www.astrouw.edu.pl/ogle/ogle4/ews'
KMTNET_URL = 'https://kmtnet.kasi.re.kr/ulens/event/{year}/listpage.dat'
MOA_PRIME_URL = 'https://moaprime.massey.ac.nz/alerts/index/prime/{year}'

VIZIER_CATALOGS = {
    'MACHO': 'J/ApJ/631/906',
    'EROS2': 'J/A+A/454/185',
}

class MicrolensingCoordsBroker:
    """Ingest coordinate and targets into the OPM database.
       Purpose: cross-match through validator and ZTF/LSST matched targets 

    """

    name = 'MicrolensingCoords'

    def fetch_alerts(self, years=None, surveys='all'):
        if years is None:
            years = [str(Time.now().byear)[:4]]

        all_surveys = ['OGLE', 'KMTNET', 'MACHO', 'EROS2'] #MOAPRIME missing...
        if str(surveys).lower() == 'all':
            survey_list = all_surveys
        else:
            survey_list = [surveys] if isinstance(surveys, str) else surveys

        results = {}
        for survey in survey_list:
            if survey == 'OGLE':
                events = self.fetch_ogle_coords(years)
            elif survey == 'KMTNET':
                events = self.fetch_kmtnet_coords(years)
#            elif survey == 'MOAPRIME':
#                events = self.fetch_moa_coords(years)
            elif survey == 'MACHO':
                events = self.fetch_vizier_coords('MACHO')
            elif survey == 'EROS2':
                events = self.fetch_vizier_coords('EROS2')
            else:
                print(f'Unknown survey {survey}, skipping')
                continue

            results[survey] = self.ingest_events(events)

        return results

    def fetch_ogle_coords(self, years):
        print('Fetching OGLE event coordinates for years ' + repr(years))
        events = {}
        for year in years:
            par_file_url = os.path.join(OGLE_URL, year, 'lenses.par')
            response = requests.get(par_file_url)
            print(f'OGLE {year}: status {response.status_code}')
            if response.status_code != 200:
                continue

            for line in response.iter_lines():
                line = str(line)
                if 'StarNo' in line or len(line) <= 5:
                    continue
                entries = line.split()
                name = 'OGLE-' + entries[0].replace("b'", "")
                ra, dec = entries[3], entries[4]
                try:
                    s = SkyCoord(ra, dec, unit=(unit.hourangle, unit.deg), frame='icrs')
                    events[name] = (s.ra.deg, s.dec.deg)
                except Exception:
                    print(f'OGLE: could not parse coords for {name}')

        print(f'OGLE: found {len(events)} event(s)')
        return events

    def fetch_kmtnet_coords(self, years):
        print('Fetching KMTNet event coordinates for years ' + repr(years))
        events = {}
        for year in years:
            url = KMTNET_URL.format(year=year)
            response = requests.get(url)
            print(f'KMTNet {year}: status {response.status_code}')
            if response.status_code != 200:
                continue

            for line in response.iter_lines():
                line = line.decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                entries = line.split()
                if len(entries) < 5:
                    continue
                name = entries[0]
                ra_str, dec_str = entries[3], entries[4]
                if ":" in entries[3] and ":" in entries[4]:
                    try:
                        s = SkyCoord(ra_str, dec_str, unit=(unit.hourangle, unit.deg), frame='icrs')
                        events[name] = (s.ra.deg, s.dec.deg)
                    except Exception:
                        print(f'KMTNet: could not parse coords for {name}')

        print(f'KMTNet: found {len(events)} event(s)')
        return events
    def fetch_vizier_coords(self, survey):
        print(f'Fetching {survey} coordinates from VizieR catalog {VIZIER_CATALOGS[survey]}')
        events = {}

        v = Vizier(columns=['**'], row_limit=-1)
        catalogs = v.get_catalogs(VIZIER_CATALOGS[survey])
        if len(catalogs) == 0:
            print(f'{survey}: no catalog data retrieved')
            return events

        print(f'{survey}: retrieved tables {list(catalogs.keys())}')
        table = catalogs[0]
        print(f'{survey}: table has {len(table)} rows, columns {table.colnames}')

        id_col = 'MACHO' if survey == 'MACHO' else 'EROS2'

        for row in table:
            try:
                star_id = str(row[id_col]).strip()
                name = f'{survey}_{star_id}'

                ra_str = str(row['RAJ2000']).strip()
                dec_str = str(row['DEJ2000']).strip()

                s = SkyCoord(ra_str, dec_str, unit=(unit.hourangle, unit.deg), frame='icrs')
                events[name] = (s.ra.deg, s.dec.deg)
            except Exception as e:
                print(f'{survey}: could not parse row {row}: {e}')

        print(f'{survey}: found {len(events)} event(s)')
        return events


    def ingest_events(self, events, debug=False):
        
        print(f'Ingesting {len(events)} event(s)')
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
        list_of_targets = []
        new_targets = []

        for event_name, (ra, dec) in events.items():
            qs = GalacticTarget.objects.filter(name=event_name)
            if len(qs) == 0:
                target, result = validators.get_or_create_event(event_name, ra, dec, debug=debug)
                if result == 'new_target':
                    print(f'Added event {event_name}')
                    new_targets.append(target)
                    filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                    filtered_target.update(permissions=GalacticTarget.Permissions.PUBLIC)
                    try:
                        with transaction.atomic():
                            filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                            pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)
                            filtered_target.update(expected_visits=visit_map[pixel_index])
                    except Exception:
                        print('Expected visits failed for ' + target.name)
            else:
                print(f'Found {qs.count()} existing target(s) with name {event_name}')
                target = qs[0]

            list_of_targets.append(target)

        print(f'Completed ingest: {len(new_targets)} new target(s) of {len(list_of_targets)} total')
        return list_of_targets, new_targets
