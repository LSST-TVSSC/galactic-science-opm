import re

from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG, get_var_star_variability_analysis
from custom_code.variability.VariabilityFlagsClient import VariabilityFlagsClient


class VizierVariabilityFlagsClient(VariabilityFlagsClient):

    def get_variability_info_for_targets(self, targets):
        results = dict()
        success = False
        flags = []
        for target in targets:
            result = get_var_star_variability_analysis(target.ra, target.dec)
            if result == NOT_IN_ANY_CATALOG or result == "":
                flags = []
                success = True
            else:
                if re.match(r"^Error Vizier query", result):
                    pass
                else:
                    flags = result.split(",")
                    success = True
            results[target.name] = {
                "name": target.name,
                "flags": flags,
                "success": success,
            }

        return results

