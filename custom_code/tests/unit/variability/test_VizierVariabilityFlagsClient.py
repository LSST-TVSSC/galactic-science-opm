from os import path
import pickle
import astropy.units as unit
from astropy.coordinates import SkyCoord
from unittest import mock

from django.test import TransactionTestCase

from custom_code.target_models import GalacticTarget
from custom_code.variability.VizierVariabilityFlagsClient import (
    VizierVariabilityFlagsClient,
)


class TestVizierVariabilityFlagsClient(TransactionTestCase):
    def test_should_return_variability_flags_correctly(
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
            "ZTF21abasvhl": {
                "name": "ZTF21abasvhl",
                "success": True,
                "flags": ["ECL", "dubious"],
            },
            "ZTF19adcrpjd": {
                "name": "ZTF19adcrpjd",
                "success": True,
                "flags": ["ECL", "dubious"],
            },
        }
        EXPECTED_RADIUS = 3 * unit.arcsec

        with mock.patch("custom_code.utils.catalog_requests.Vizier") as mocked:
            # GIVEN a Vizier instants returning valid results
            data_folder = path.join("custom_code", "tests", "mocks", "responses")

            def replacement(*args, **kwargs):
                VIZIER_QUERY_REGION_PICKLE = path.join(
                    data_folder, "vizier__query_region_variability.pkl"
                )
                with open(VIZIER_QUERY_REGION_PICKLE, "rb") as f:
                    result = pickle.load(f)
                return result

            instance = mocked.return_value
            instance.query_region.side_effect = replacement
            variability_flags_client = VizierVariabilityFlagsClient()

            # WHEN the variability is requested
            actual_result = variability_flags_client.get_variability_info_for_targets(
                TARGETS
            )
            # THEN the info should be provided in the correct format
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)

            # AND the third party API should be called correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)

    def test_should_return_empty_on_no_results(
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
            "ZTF21abasvhl": {
                "name": "ZTF21abasvhl",
                "success": True,
                "flags": [],
            },
            "ZTF19adcrpjd": {
                "name": "ZTF19adcrpjd",
                "success": True,
                "flags": [],
            },
        }
        EXPECTED_RADIUS = 3 * unit.arcsec

        with mock.patch("custom_code.utils.catalog_requests.Vizier") as mocked:
            # GIVEN a Vizier instance that returns None for query_region
            def replacement(*args, **kwargs):
                return None

            instance = mocked.return_value
            instance.query_region.side_effect = replacement
            variability_flags_client = VizierVariabilityFlagsClient()

            # WHEN the info is requested
            actual_result = variability_flags_client.get_variability_info_for_targets(
                TARGETS
            )

            # THEN results should indicate success but return an empty list
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)

            # AND the third party API should be called correctly
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)

    def test_should_return_empty_and_success_false_on_exception(
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
            "ZTF21abasvhl": {
                "name": "ZTF21abasvhl",
                "success": False,
                "flags": [],
            },
            "ZTF19adcrpjd": {
                "name": "ZTF19adcrpjd",
                "success": False,
                "flags": [],
            },
        }
        EXPECTED_RADIUS = 3 * unit.arcsec

        with mock.patch("custom_code.utils.catalog_requests.Vizier") as mocked:
            # GIVEN a vizier instance that raises an for query_region
            def replacement(*args, **kwargs):
                raise Exception("Vizier mock raised exception on purpose")

            instance = mocked.return_value
            instance.query_region.side_effect = replacement
            variability_flags_client = VizierVariabilityFlagsClient()

            # WHEN the info is requested
            actual_result = variability_flags_client.get_variability_info_for_targets(
                TARGETS
            )

            # THEN success should be false and empty list should be returned
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            for i, call_args in enumerate(instance.query_region.call_args_list):
                target = TARGETS[i]
                ra, dec = target.ra, target.dec
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)

    def test_should_return_empty_and_success_false_on_exception_of_Vizier_init(
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
            "ZTF21abasvhl": {
                "name": "ZTF21abasvhl",
                "success": False,
                "flags": [],
            },
            "ZTF19adcrpjd": {
                "name": "ZTF19adcrpjd",
                "success": False,
                "flags": [],
            },
        }

        # GIVEN a vizier instance that raises an exception upon creation
        class Dummy:
            def __init__(self, *args, **kwargs) -> None:
                raise Exception("Vizier mock raised exception on purpose")

        def provide():
            return Dummy

        with mock.patch(
            "custom_code.utils.catalog_requests.Vizier", new_callable=provide
        ):
            variability_flags_client = VizierVariabilityFlagsClient()

            # WHEN the info is requested
            actual_result = variability_flags_client.get_variability_info_for_targets(
                TARGETS
            )
            # THEN success should be false and the results should be empty
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
