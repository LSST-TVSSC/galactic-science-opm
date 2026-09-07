from abc import ABC, abstractmethod


class ExtragalacticInfoApi(ABC):
    @abstractmethod
    def check_glade_plus_for_targets(self, targets):
        """ 
        Needs implementation. 
        {
            "ZTF26abdwauc": {
                "success": True,
                "count": 42,
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "count": 42,
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "count": 42,
                "name": "ZTF26abeziup",
            },
        }
        """
