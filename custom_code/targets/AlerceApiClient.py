
from alerce.core import Alerce
from astropy.time import Time
from custom_code.tests.helpers import make_pickle_from_data
import pandas as pd

from custom_code.targets.TargetApiClient import TargetApiClient


class AlerceApiClient(TargetApiClient):
    def __init__(self):
        pass

    def _fetch_alerts(self, survey, class_name, days=10, start_date=None):
        if start_date is None:
            start_date = int(Time.now().mjd)

        alerce = Alerce()
        not_at_end_of_pages = True
        current_page = 1
        alerce_results = []
        while not_at_end_of_pages:
            alerce_results_page = alerce.query_objects(
                classifier="lc_classifier_BHRF_forced_phot",
                class_name=class_name,
                format="pandas",
                firstmjd=float(start_date - days),
                page=current_page,
                order_by="probability",
                order_mode="DESC",
                survey=survey,
            )
            if alerce_results_page.empty:
                not_at_end_of_pages = False
            else:
                alerce_results.append(alerce_results_page)
                current_page += 1

        if len(alerce_results) > 0:
            alerce_results = pd.concat(alerce_results, ignore_index=True)
        else:
            alerce_results = pd.DataFrame(alerce_results)

        return alerce_results

    def fetch_potential_targets(self, class_name, survey, start_date, since_n_days):
        converted_results = []

        results = self._fetch_alerts(
            survey="ztf",
            class_name=class_name,
            days=since_n_days,
            start_date=start_date,
        )

        for _, result in results.iterrows():
            converted_results.append(
                {
                    "name": result["oid"],
                    "ra": result["meanra"],
                    "dec": result["meandec"],
                    "known_aliases": [],
                    "lightcurve": [],
                    "survey": survey,
                }
            )

        return converted_results

