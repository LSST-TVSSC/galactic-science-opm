from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError

from tom_alerts.alerts import Target
from tom_dataproducts.models import PhotometryReducedDatum


class PhotometryCreator:
    def create_photometry_for_targets(self, photometry_candidates):
        createds = []
        errors = []
        for c in photometry_candidates:
            target = Target.objects.get(name=c.location)
            try:
                datum, _ = PhotometryReducedDatum.objects.update_or_create(
                    brightness=c.magnitude,
                    bandpass=c.filter,
                    brightness_error=c.error,
                    source_location=c.location,
                    timestamp=c.timestamp,
                    source_name=c.source,
                    target=target,
                )
                createds.append(datum)
            except IntegrityError as e:
                if "unique_photometry" in str(e):
                    pass

            except Exception as e:
                message = ('ALERCE HARVERSTER: Exception occured while ingesting photometry')
                message += (e.__class__.__name__)
                message += str(e)
                error = {"message": message, "target": target.name}
                errors.append(error)

        return errors, createds
