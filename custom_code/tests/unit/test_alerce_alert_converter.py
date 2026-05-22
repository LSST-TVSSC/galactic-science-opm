from unittest import TestCase
from astropy.coordinates import SkyCoord
import astropy.units as unit

# A possible implementation. Should go into different folder.
def alerce_alert_converter(name, ra, dec):
    coordinates = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame='icrs')
    return {
        "name": name,
        "ra": float(coordinates.ra.deg),
        "dec": float(coordinates.dec.deg)
    }

# python manage.py test custom_code.tests.unit --settings=galactic_science_opm.settings_test
class AlerceAlertConverterTests(TestCase):
    def test_converts_alerce_alert_to_dto(self):
        TARGET_TO_TEST = "ZTF26aarbgfh"
        expected = {
            "name": TARGET_TO_TEST,
            "ra": 274.577805040264,
            "dec": 2.056956216712028
        }
        converted = alerce_alert_converter(TARGET_TO_TEST, 274.577805040264, 2.056956216712028)
        self.assertEquals(expected, converted)
