from abc import ABC, abstractmethod


class PhotometryApiClient(ABC):
    @abstractmethod
    def fetch_photometry_for_targets(self, targets, survey):
        """ 
        Needs implementation. 
        Returns a list of PhotometryCandidate. 
        """

class PhotometryCandidate:
    def __init__(self, magnitude, filter, error, location, timestamp, source):
        self.magnitude = magnitude
        self.filter = filter
        self.error = error
        self.location = location
        self.timestamp = timestamp
        self.source = source

    def __str__(self):
        s = (
            f"{self.location}: mag: {self.magnitude}, filter: {self.filter}, error: {self.error}, "
            f"timestamp: {self.timestamp} , source: {self.source}"
        )
        return s

    def __eq__(self, other):
        return (
            self.magnitude == other.magnitude
            and self.filter == other.filter
            and self.error == other.error
            and self.location == other.location
            and self.source == other.source
            and self.timestamp == other.timestamp
        )


