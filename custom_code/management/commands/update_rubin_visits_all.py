from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from guardian.shortcuts import assign_perm
from django.apps import apps
from django.db import transaction
import astropy.units as unit
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord, Angle
import healpy as hp
from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.utils.catalog_requests import get_glade_plus_count
from custom_code.utils.catalog_requests import get_var_star_variability_analysis

class Command(BaseCommand):
    help = 'Update top 100 expected Rubin obs and check for GLADE+, variability'
    
    def handle(self, *args, **options):
        config = apps.get_app_config('custom_code')
        visit_map = config.nvisits_10yrs_map
      
        distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='T').filter(average_master_probability__gt=0.)
        qs = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').distinct()[:100]
        for entry in qs:
            target = GalacticTarget.objects.filter(name__icontains=entry.target.name).last()
            s = SkyCoord(target.ra, target.dec, unit=(unit.deg, unit.deg), frame='icrs')
            result = get_glade_plus_count(s)
            with transaction.atomic():
                filtered_target = GalacticTarget.objects.filter(name__icontains=target)
                pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)             
                filtered_target.update(expected_visits = visit_map[pixel_index])
                if result > 0:
                    filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.IN_GLADE_PLUS)
                elif result == 0:
                    filtered_target.update(known_extragalactic = GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS)
                if "ZTF" in target.name or "LSST_" in target.name:
                    result_var_vizier=get_var_star_variability_analysis(target.ra, target.dec)
                    if result_var_vizier!="" and result_var_vizier!=None:
                        filtered_target.update(known_variability = result_var_vizier)
                    else:
                        filtered_target.update(known_variability = "None, queried")
