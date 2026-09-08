from abc import ABC, abstractmethod


class VariabilityFlagsClient(ABC):
    @abstractmethod
    def get_variability_info_for_targets(self, targets):
        """ 
        Needs implementation. 
        Returns dict with the following structure:
        {
            "ZTF26abdwauc": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF26abeziup",
            },
        }

        """
