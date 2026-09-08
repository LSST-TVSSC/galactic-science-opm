from abc import ABC, abstractmethod


class ExpectedVisitsApiClient(ABC):
    @abstractmethod
    def get_expected_visits_for_targets(self, targets):
        """ 
        Needs implementation. 
        Returns dict the following structure:
         {
            "ZTF26abdwauc": {
                "success": True,
                "visits": 42,
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "visits": 42,
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "visits": 42,
                "name": "ZTF26abeziup",
            },
        }

        """

