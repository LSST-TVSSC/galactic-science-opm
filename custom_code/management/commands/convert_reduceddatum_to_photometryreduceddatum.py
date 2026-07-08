from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from tom_dataproducts.models import PhotometryReducedDatum, ReducedDatum


class Command(BaseCommand):
    help = "Convert existing photometry ReducedDatums to PhotometryReducedDatum"

    def add_arguments(self, parser):
        parser.add_argument("target_names", nargs="*", type=str)

    def handle(self, *args, **options):
        reduceddatums_for_target = ReducedDatum.objects.all()
        for reduceddatum in reduceddatums_for_target:
            values = reduceddatum.value
            brightness = values["magnitude"]
            brightness_error = values["error"]
            limit = None
            unit = ""
            bandpass = values["filter"]
            exposure_time = None
            timestamp = reduceddatum.timestamp
            target = reduceddatum.target
            try:
                with transaction.atomic():
                    _, created = PhotometryReducedDatum.objects.update_or_create(
                        brightness=brightness,
                        brightness_error=brightness_error,
                        limit=limit,
                        unit=unit,
                        bandpass=bandpass,
                        exposure_time=exposure_time,
                        timestamp=timestamp,
                        target=target,
                        source_name=reduceddatum.source_name,
                        source_location=reduceddatum.source_location,
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Successfully converted ReducedDatum with pk {reduceddatum.id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Successfully updated PhotometryReducedDatum with pk {reduceddatum.id}"
                            )
                        )

            except IntegrityError as e:
                if "duplicate key" in str(e):
                    self.stdout.write(
                        self.style.NOTICE(
                            f"Skipping ReducedDatum with pk {reduceddatum.id} as it already exists"
                        )
                    )
                    continue
                else:
                    print(
                        f"There was a problem migrating PhotometryReducedDatum for pk: {reduceddatum.id}"
                    )
                    print(e.__class__.__name__)
                    print(e)
                    continue

            except Exception as e:
                print(
                    f"There was a problem migrating PhotometryReducedDatum for pk: {reduceddatum.id}"
                )
                print(e.__class__.__name__)
                print(e)
                continue
