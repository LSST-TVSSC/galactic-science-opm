from django.core.management.base import BaseCommand
from tom_dataproducts.models import PhotometryReducedDatum, ReducedDatum


def convert_all_reduceddatum_to_photometryreduceddatum():
    BATCH_SIZE = 2500
    conversion_candiates = list()
    creation_counter = 0
    reduceddatums_for_target = ReducedDatum.objects.iterator(chunk_size=BATCH_SIZE)
    number_of_reduceddatums = ReducedDatum.objects.count()
    errors = list()

    for reduceddatum in reduceddatums_for_target:
        try:
            values = reduceddatum.value
            brightness = values["magnitude"]
            brightness_error = values["error"]
            limit = None
            unit = ""
            bandpass = values["filter"]
            exposure_time = None
            timestamp = reduceddatum.timestamp
            target = reduceddatum.target

            if len(bandpass) > 32:
                errors.append(
                    f"Could not convert ReducedDatum with pk {reduceddatum.id}: "
                    "Value for filter too long"
                )
                continue

            convertee = PhotometryReducedDatum(
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
            conversion_candiates.append(convertee)

            if len(conversion_candiates) == BATCH_SIZE:
                try:
                    created = PhotometryReducedDatum.objects.bulk_create(
                        conversion_candiates, ignore_conflicts=True
                    )
                    creation_counter += len(created)
                    conversion_candiates.clear()
                    print(f"Created {creation_counter} of {number_of_reduceddatums}...")
                except Exception as e:
                    print(
                        f"could not convert batch of conversion_candiates ({len(conversion_candiates)}"
                    )
                    print(e.__class__.__name__)
                    print(e)

        except Exception as e:
            print(f"could not convert reduceddatum with pk {reduceddatum.id}")
            print(e.__class__.__name__)
            print(e)

    # insert remaining ones
    if conversion_candiates:
        try:
            created = PhotometryReducedDatum.objects.bulk_create(
                conversion_candiates, ignore_conflicts=True
            )
            creation_counter += len(created)
            print(f"Created {creation_counter} of {number_of_reduceddatums}...")
        except Exception as e:
            print(
                f"could not convert final batch of conversion_candiates ({len(conversion_candiates)}"
            )
            print(e.__class__.__name__)
            print(e)

    print(
        f"Converted {creation_counter} of {number_of_reduceddatums} ReducedDatums"
        f" to PhotometryReducedDatum"
    )
    if len(errors) > 0:
        print(f"{len(errors)} filter values were too long.")
        print(errors)


class Command(BaseCommand):
    help = "Convert existing photometry ReducedDatums to PhotometryReducedDatum"

    def add_arguments(self, parser):
        parser.add_argument("target_names", nargs="*", type=str)

    def handle(self, *args, **options):
        convert_all_reduceddatum_to_photometryreduceddatum()
