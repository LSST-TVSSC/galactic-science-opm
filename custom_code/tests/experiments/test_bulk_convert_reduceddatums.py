from datetime import date, datetime, timedelta
import random
from zoneinfo import ZoneInfo
from django.test import TestCase, TransactionTestCase
from tom_dataproducts.models import ReducedDatum
from custom_code.management.commands.convert_reduceddatum_to_photometryreduceddatum import convert_all_reduceddatum_to_photometryreduceddatum
from custom_code.target_models import GalacticTarget

def create_dummy_reduceddatums(amount, add_too_long_filter = False):
    BATCH_SIZE = 5000
    batch = []
    creation_counter = 0
    filter_values = ["r","g","b"]

    if add_too_long_filter:
        filter_values.append("ThisIsAVeryVeryVeryLongValueForAFilterThatShouldNotBeConvertedAndInsteadBeSkipped")

    target = GalacticTarget.objects.create(name="foo")
    dummy_datums = [
        ReducedDatum(
            target=target, 
            timestamp=datetime.now(ZoneInfo("UTC")) - timedelta(days=amount-i), 
            value={
                "magnitude": random.uniform(12, 15),
                "error": random.uniform(1, 5),
                "filter": random.choice(filter_values)
            }
        )
        for i in range(amount)
    ]


    for rd in dummy_datums:
        batch.append(rd)

        if len(batch) == BATCH_SIZE:
            created = ReducedDatum.objects.bulk_create(batch)
            creation_counter += len(created)
            batch.clear()
            print(f"Created {creation_counter} of {len(dummy_datums)}...")

    if batch:
        created = ReducedDatum.objects.bulk_create(batch)
        creation_counter += len(created)
        print(f"Created {creation_counter} of {len(dummy_datums)}...")

    print("Created all dummy_data")
    dummy_datums.clear()

# python manage.py test custom_code.experiments --settings=galactic_science_opm.settings_test
class PhotometryReducedDatumConverterTest(TransactionTestCase):
    def test_creates_photometryreduceddatums_in_bulk(self):
        create_dummy_reduceddatums(2_000_000)
        convert_all_reduceddatum_to_photometryreduceddatum()
        # self.assertEquals(len(actual_total), len(expected_total))
        # self.assertEquals(len(actual_new), len(expected_new))
