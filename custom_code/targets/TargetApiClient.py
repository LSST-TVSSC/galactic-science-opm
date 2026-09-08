from abc import ABC, abstractmethod


class TargetApiClient(ABC):
    @abstractmethod
    def fetch_potential_targets(self, class_name, survey, start_date, since_n_days):
        """
        Needs implementation.
        Should return a list of dicts with the following structure:
        [
            {
                "name": "ZTF26abdwauc",
                "ra": 285.90945662498603,
                "dec": -25.534577312499998,
                "known_aliases": [],
                "lightcurve": [],
                "survey": "ztf",
            }
        ]
        """
