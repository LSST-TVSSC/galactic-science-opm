from abc import ABC, abstractmethod


class VariabilityFlagsClient(ABC):
    @abstractmethod
    def get_variability_info_for_targets(self, targets):
        """ Needs implementation. """
