from django.db import models
from tom_targets.base_models import TargetMatchManager

class EventMatchManager(TargetMatchManager):
    """
    Function to check for duplications of targets already known to the database.
    This check is based on radial separation with a pre-defined exclusion radius.

    Parameter:
    target  CustomTarget    Single Target object

    Returns:
        queryset   Set of known Targets within the match radius.
    """

    def match_target(self, target, *args, **kwargs):
        """
        Check for known Targets by RA, Dec within a radius of 2 arcsec
        """
        queryset = super().match_target(target, *args, **kwargs)

        search_radius = 2.0 # arcsec

        cone_search_queryset = self.match_cone_search(target.ra, target.dec, search_radius)

        return queryset | cone_search_queryset

