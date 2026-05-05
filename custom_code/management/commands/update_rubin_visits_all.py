from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm
from django.apps import apps
from django.db import transaction
from astropy.time import Time, TimezoneInfo
import astropy.units as unit
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord, Galactic, Angle
import healpy as hp
from custom_code.target_models import GalacticTarget

class Command(BaseCommand):
    help = 'Update all expected Rubin obs and check for GLADE+'
    
    def handle(self, *args, **options):
        qs = GalacticTarget.objects.all()
        target_list = list(set(qs))
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
        
        for target in target_list:

            s = SkyCoord(target.ra, target.dec, unit=(unit.deg, unit.deg), frame='icrs')
            result = Vizier.query_region(s,radius=Angle(1.5 / 60. / 60., "deg"), catalog='VII/281', cache=False)
            extragalactic_catalog_flag = "not in GLADE+"
            if (len(result) > 0):
                extragalactic_catalog_flag = f"in GLADE+"
            print(target,extragalactic_catalog_flag)
            with transaction.atomic():
                filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                filtered_target.update(expected_visits = visit_map[pixel_index])
                filtered_target.update(known_extragalactic = extragalactic_catalog_flag)
               
            target.save()