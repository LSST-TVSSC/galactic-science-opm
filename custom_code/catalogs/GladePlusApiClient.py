from astropy.coordinates import SkyCoord
import astropy.units as unit
from astroquery.vizier import Vizier
from custom_code.utils.catalog_requests import get_glade_plus_count_with_ra_dec
from tom_targets.forms import Angle

from custom_code.catalogs.ExtragalacticInfoApiClient import ExtragalacticInfoApi


class GladeClientApi(ExtragalacticInfoApi):
    def _make_glade_info(self, success, count, name):
        return {"success": success, "count": count, "name": name}

    def check_glade_plus_for_targets(self, targets):
        results = dict()
        for target in targets:
            name, ra, dec = target.name, target.ra, target.dec

            result = get_glade_plus_count_with_ra_dec(ra, dec)
            if result == 0:
                results[target.name] = self._make_glade_info(
                    success=True, name=name, count=0
                )
            elif result == -1:
                results[target.name] = self._make_glade_info(
                    success=False, name=name, count=0
                )
            else:
                results[target.name] = self._make_glade_info(
                    success=True, name=name, count=result
                )

        return results

