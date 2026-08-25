import collections
from unittest import mock

from django.test import TransactionTestCase

from custom_code.observations.HealpyExpectedVisitsClient import HealpyExpectedVisitsClient
from custom_code.target_models import GalacticTarget


class TestHealpyExpectedVisitsClient(TransactionTestCase):
    def test_should_report_expected_visits_correctly(
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
            "ZTF21abasvhl": {"name": "ZTF21abasvhl", "visits": 42, "success": True},
            "ZTF19adcrpjd": {"name": "ZTF19adcrpjd", "visits": 42, "success": True},
        }

        with (
            mock.patch(
                "custom_code.observations.HealpyExpectedVisitsClient.hp.ang2pix"
            ) as mocked_ang2pix,
            mock.patch(
                "custom_code.observations.HealpyExpectedVisitsClient.apps.get_app_config",
            ) as mocked_get_app_config,
        ):
            # GIVEN an app config WHICH returns [42] for nvisits_10yrs_map
            FakeAppConfig = collections.namedtuple("FakeAppConfig", "nvisits_10yrs_map")
            fake_config = FakeAppConfig([42])
            # AND an ang2pix implementation that returns 0 (used as index for [42], thus returning 42)
            mocked_ang2pix.return_value = 0
            def provide_it(*args, **kwargs):
                return fake_config
            mocked_get_app_config.side_effect = provide_it
            expected_visits_client = HealpyExpectedVisitsClient()

            # WHEN the visits are requested
            actual_result = expected_visits_client.get_expected_visits_for_targets(
                TARGETS
            )

            # THEN the results should contain the correct values
            self.assertDictEqual(actual_result, EXPECTED_RESULTS)
            # AND the third party API should be called correctly
            for i, call in enumerate(mocked_ang2pix.call_args_list):
                self.assertEqual(call.args[0], 128)
                self.assertEqual(call.args[1], TARGETS[i].ra)
                self.assertEqual(call.args[2], TARGETS[i].dec)
                self.assertEqual(call.kwargs["lonlat"], True)
                self.assertEqual(call.kwargs["nest"], True)

