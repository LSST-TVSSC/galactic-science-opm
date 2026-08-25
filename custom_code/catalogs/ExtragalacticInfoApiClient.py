from abc import ABC, abstractmethod


class ExtragalacticInfoApi(ABC):
    @abstractmethod
    def check_glade_plus_for_targets(self, targets):
        """ Needs implementation. """
