from unittest import mock

from astropy.coordinates import SkyCoord
from django.test import TransactionTestCase
from tom_targets.forms import Angle

from custom_code.catalogs.GladePlusApiClient import GladeClientApi
from custom_code.target_models import GalacticTarget
from custom_code.tests.mocks.external.VizierMock import VizierMock
import astropy.units as unit

class TestGlasePlusClientApi(TransactionTestCase):
    def test_should_return_dict_with_results_if_vizier_has_results(
        self,
    ):

        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        EXPECTED_RESULTS = {
            "ZTF21abasvhl": {"name": "ZTF21abasvhl", "count": 1, "success": True},
            "ZTF19adcrpjd": {"name": "ZTF19adcrpjd", "count": 1, "success": True},
        }

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.utils.catalog_requests.Vizier"
        ) as mocked:
            # GIVEN a Vizier implementation that for each targets returns
            # a TableList with 1 table
            replacement = VizierMock()
            instance = mocked.return_value
            instance.query_region.side_effect = replacement.query_region
            glade_checker = GladeClientApi()

            # WHEN the testee is called
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)
            # THEN it should return the expected results
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            # AND call the third party API correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    def test_should_return_count_if_none_is_result(
        self,
    ):

        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        EXPECTED_RESULTS = {
            "ZTF21abasvhl": {"name": "ZTF21abasvhl", "count": 0, "success": True},
            "ZTF19adcrpjd": {"name": "ZTF19adcrpjd", "count": 0, "success": True},
        }

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.utils.catalog_requests.Vizier"
        ) as mocked:
            # GIVEN a Vizier implementation that return none for query_region
            instance = mocked.return_value
            def none_returning_vizier(*args, **kwargs):
                return None
            
            instance.query_region.side_effect = none_returning_vizier
            glade_checker = GladeClientApi()
            # WHEN the testee is called 
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)
            # THEN the results should match the expected ones
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            # AND the third party API should be called correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    def test_should_return_count_0_if_empty_results(
        self,
    ):

        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        EXPECTED_RESULTS = {
            "ZTF21abasvhl": {"name": "ZTF21abasvhl", "count": 0, "success": True},
            "ZTF19adcrpjd": {"name": "ZTF19adcrpjd", "count": 0, "success": True},
        }

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.utils.catalog_requests.Vizier"
        ) as mocked:
            # GIVEN a mock Vizier implementation that returns an empty list
            instance = mocked.return_value
            def none_returning_vizier(*args, **kwargs):
                return []

            instance.query_region.side_effect = none_returning_vizier
            glade_checker = GladeClientApi()

            # WHEN the testee is called
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)

            # THEN the expected results should be returned
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            # AND the third party API should be called correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    def test_should_return_success_false_if_exception(
        self,
    ):

        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        EXPECTED_RESULTS = {
            "ZTF21abasvhl": {"name": "ZTF21abasvhl", "count": 0, "success": False},
            "ZTF19adcrpjd": {"name": "ZTF19adcrpjd", "count": 0, "success": False},
        }

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.utils.catalog_requests.Vizier"
        ) as mocked:
            # GIVEN a mock Vizier implementation that raises an exception when query_region is called
            instance = mocked.return_value
            def exception_raising_mock(*args, **kwargs):
                raise Exception('This throws')

            instance.query_region.side_effect = exception_raising_mock
            glade_checker = GladeClientApi()

            # WHEN the testee is called 
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)

            # THEN the expected results should be returned
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            # AND the third party API shold be called correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)
