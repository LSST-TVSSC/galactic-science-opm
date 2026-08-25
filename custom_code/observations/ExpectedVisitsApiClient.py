from abc import ABC, abstractmethod


class ExpectedVisitsApiClient(ABC):
    @abstractmethod
    def get_expected_visits_for_targets(self, targets):
        """ Needs implementation. """

