from unittest import mock
from astropy.coordinates import SkyCoord
from astroquery.vizier import Vizier
from django.core import management
from django.test import TransactionTestCase
from tom_targets.forms import Angle
from custom_code.target_models import GalacticTarget
from custom_code.tests.experiments.mocks.Session_mock import (
    SessionMock,
)

import astropy.units as unit


class GladePlusChecker:
    def check_glade_plus_for_targets(self, targets):
        results = list()
        for target in targets:
            name, ra, dec = target
            sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")

            radius = Angle(1.5 / 60.0 / 60.0, "deg")
            try:
                vizier = Vizier()
                result = vizier.query_region(
                    sky_coords, radius=radius, catalog="VII/281", cache=False
                )
                if not result or len(result) == 0:
                    results.append((name, 0))
                else:
                    results.append((name, len(result[0])))
            except Exception as e:
                print("Error while fetching glade plus count")
                print(e.__class__.__name__)
                print(e)
                results.append((name, -1))

        return results


# python manage.py test custom_code.tests.integration.test_ingest_ztf_mocked --settings=galactic_science_opm.settings_test
class TestIngestScript(TransactionTestCase):
    # these use an old dependency and need to be reimplemented for the new version
    def test_should_create_dict_with_glade_results_if_vizier_has_results(self):

        TARGETS = [
            ("ZTF21abasvhl", 209.84372587578667, 47.12126690610595),
            ("ZTF19adcrpjd", 292.67285206700393, -19.370104587239602),
        ]

        EXPECTED_RESULTS = [("ZTF21abasvhl", 1), ("ZTF19adcrpjd", 1)]

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.tests.integration.test_ingest_ztf_mocked.Vizier"
        ) as mocked:
            replacement = VizierMock()
            instance = mocked.return_value
            instance.query_region.side_effect = replacement.query_region

            glade_checker = GladePlusChecker()
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)
            self.assertListEqual(actual_result, EXPECTED_RESULTS)
            for i, call_args in enumerate(instance.query_region.call_args_list):
                _, ra, dec = TARGETS[i]
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    def test_should_create_dict_with_glade_results_if_vizier_also_has_empty_results(
        self,
    ):

        TARGETS = [
            ("ZTF21abasvhl", 209.84372587578667, 47.12126690610595),
            ("ZTF19adcrpje", 292.67285206700393, -19.370104587239602),
            ("ZTF19adcrpjf", 292.67285206700394, -19.370104587239603),
        ]

        EXPECTED_RESULTS = [
            ("ZTF21abasvhl", 1),  # expected if there is a result
            ("ZTF19adcrpje", 0),  # expected if len of results is 0
            ("ZTF19adcrpjf", 0),  # expected if result is None
        ]

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.tests.integration.test_ingest_ztf_mocked.Vizier"
        ) as mocked:
            call_counter = 0

            def mocked_function(*args, **kwargs):

                nonlocal call_counter
                result = None

                if call_counter == 0:
                    result = [[1]]
                elif call_counter == 1:
                    result = []
                else:
                    result = None
                call_counter += 1
                return result

            instance = mocked.return_value
            instance.query_region.side_effect = mocked_function

            glade_checker = GladePlusChecker()
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)
            self.assertListEqual(actual_result, EXPECTED_RESULTS)
            for i, call_args in enumerate(instance.query_region.call_args_list):
                _, ra, dec = TARGETS[i]
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    def test_should_create_dict_with_glade_results_if_exception_raised(self):

        TARGETS = [
            ("ZTF21abasvhl", 209.84372587578667, 47.12126690610595),
        ]

        EXPECTED_RESULTS = [
            ("ZTF21abasvhl", -1),  # expected if an exception is raised
        ]

        EXPECTED_RADIUS = Angle(1.5 / 60.0 / 60.0, "deg")

        with mock.patch(
            "custom_code.tests.integration.test_ingest_ztf_mocked.Vizier"
        ) as mocked:

            def throwing_function(*args, **kwargs):
                raise Exception("Oopsi")

            instance = mocked.return_value
            instance.query_region.side_effect = throwing_function

            glade_checker = GladePlusChecker()
            actual_result = glade_checker.check_glade_plus_for_targets(TARGETS)
            self.assertListEqual(actual_result, EXPECTED_RESULTS)
            for i, call_args in enumerate(instance.query_region.call_args_list):
                _, ra, dec = TARGETS[i]
                sky_coords = SkyCoord(ra, dec, unit=(unit.deg, unit.deg), frame="icrs")
                self.assertTrue(call_args.args[0] == sky_coords)
                self.assertTrue(call_args.kwargs["radius"] == EXPECTED_RADIUS)
                self.assertEqual(call_args.kwargs["catalog"], "VII/281")
                self.assertEqual(call_args.kwargs["cache"], False)

    # testing this whole command is next to impossible
    # There are too many interactions with APIs and mocking
    # this is too complicated
    def alerce_ztf(self):

        with mock.patch(
            "requests.Session",
            new_callable=lambda: SessionMock,
        ):
            prev_targets = GalacticTarget.objects.count()
            _ = management.call_command("ingest_alerce_ztf_lightcurves", "ZTF26", "2")
            post_target = GalacticTarget.objects.count()
            self.assertGreater(post_target, prev_targets)
            self.assertEqual(post_target, 56)
