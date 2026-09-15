import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from astropy.coordinates import SkyCoord
from astropy import units as u

from custom_code.target_models import GalacticTarget

KMT_URLS = {
    2024: 'https://kmtnet.kasi.re.kr/ulens/event/2024/listpage.dat',
    2025: 'https://kmtnet.kasi.re.kr/ulens/event/2025/listpage.dat',
}

def parse_kmt_line(line):
    """Extract event name, RA and Dec from listpage.dat."""
    entries = line.split()
    if not entries:
        return None

    name = entries[0]
    if not name.startswith('KMT-'):
        return None

    ra = dec = None
    for i, tok in enumerate(entries):
        if ':' in tok and i + 1 < len(entries) and ':' in entries[i + 1]:
            ra = tok
            dec = entries[i + 1]
            break

    if ra is None or dec is None:
        return None

    return name, ra, dec


def fetch_kmt_coords(year):
    """Download and parse the KMT listpage.dat file for a given year."""
    url = KMT_URLS[year]
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    coords = {}
    for line in response.text.splitlines():
        parsed = parse_kmt_line(line)
        if parsed:
            name, ra, dec = parsed
            coords[name] = (ra, dec)

    return coords

class Command(BaseCommand):
    help = 'Fix misidentified RA/Dec coordinates for KMT-2024 and KMT-2025 targets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--years', nargs='+', type=int, default=[2024, 2025],
            help='Years to fix (default: 2024 2025)'
        )

    def handle(self, *args, **options):
        years = options['years']

        for year in years:
            try:
                coords = fetch_kmt_coords(year)
            except Exception as e:
                self.stderr.write(f'Failed to fetch/parse KMT {year} list: {e}')
                continue

            for name, (ra_str, dec_str) in coords.items():
                try:
                    target = GalacticTarget.objects.get(name=name)
                except GalacticTarget.DoesNotExist:
                    continue
                except GalacticTarget.MultipleObjectsReturned:
                    self.stderr.write(f'Multiple targets found for {name}, skipping')
                    continue

                try:
                    s = SkyCoord(ra_str, dec_str, unit=(u.hourangle, u.deg))
                except Exception as e:
                    self.stderr.write(f'Could not parse coords for {name}: {e}')
                    continue

                new_ra, new_dec = s.ra.deg, s.dec.deg

                # Skip if coordinates already match closely (< 0.1 arcsec)
                if target.ra is not None and target.dec is not None:
                    existing = SkyCoord(target.ra * u.deg, target.dec * u.deg)
                    if existing.separation(s).arcsec < 0.1:

                        continue

                with transaction.atomic():
                    target.ra = new_ra
                    target.dec = new_dec
                    target.save()

