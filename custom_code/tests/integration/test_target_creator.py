from django.test import TestCase
from custom_code.match_managers import validators
from custom_code.target_models import GalacticTarget

# A possible implementation to test. Should go in different folder
def target_creator(dtos):
    total_targets = []
    new_targets = []
    for dto in dtos:
        target, result = validators.get_or_create_event(
            dto["name"],
            dto["ra"],
            dto["dec"]
        )
        if result == "new_target":
            new_targets.append(target)

        total_targets.append(target)
    return total_targets, new_targets

# python manage.py test custom_code.tests.unit --settings=galactic_science_opm.settings_test
class TargetCreatorTests(TestCase):
    def test_create_targets_from_dtos_empty_db(self):
        TARGET_TO_TEST = "ZTF26goomba"
        TARGET_TO_TEST_2 = "ZTF26luigi"
        expected_new = [
            GalacticTarget(
                name=TARGET_TO_TEST, ra=274.577805040264, dec=2.056956216712028, id=1
            ),
            GalacticTarget(
                name=TARGET_TO_TEST_2, ra=283.1755543793785, dec=0.4623901598870619, id=2
            ),
        ]
        expected_total = expected_new
        objects_to_convert = [
            {
                "name": TARGET_TO_TEST,
                "ra": 274.577805040264, 
                "dec": 2.056956216712028
            }, 
            {
                "name": TARGET_TO_TEST_2,
                "ra": 283.1755543793785, 
                "dec": 0.4623901598870619
            }
        ]
        actual_total, actual_new = target_creator(objects_to_convert)
        self.assertEquals(len(actual_total), len(expected_total))
        self.assertEquals(len(actual_new), len(expected_new))
        for first, second in zip(actual_new, expected_new):
            result, error = galactic_target_is_equal(first, second)
            self.assertEqual(True, result, f"Both are not equal. Mismatch in field: {error}")

####### helpers #######

def galactic_target_is_equal(first, second):
    relevant_fields = ["name", "ra", "dec"]
    for field in relevant_fields:
        if getattr(first, field) == getattr(second, field):
            pass
        else:
            return False, field
    return True, None
