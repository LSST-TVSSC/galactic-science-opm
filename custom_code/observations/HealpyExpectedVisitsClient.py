from django.apps import apps

from custom_code.observations.ExpectedVisitsApiClient import ExpectedVisitsApiClient

import healpy as hp


class HealpyExpectedVisitsClient(ExpectedVisitsApiClient):
    def get_expected_visits_for_targets(self, targets):
        config = apps.get_app_config("custom_code")
        visit_map = config.nvisits_10yrs_map
        results = dict()

        for target in targets:
            pixel_index = hp.ang2pix(128, target.ra, target.dec, lonlat=True, nest=True)
            visits = visit_map[pixel_index]
            results[target.name] = {
                "name": target.name,
                "success": True,
                "visits": visits,
            }

        return results
