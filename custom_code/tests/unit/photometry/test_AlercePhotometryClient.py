import datetime
from os import path
import pandas as pd
import pickle
from unittest import mock
from astropy.time import TimezoneInfo

from django.test import TransactionTestCase

from custom_code.photometry.AlercePhotometryClient import AlercePhotometryClient
from custom_code.photometry.PhotometryApiClient import PhotometryCandidate
from custom_code.target_models import GalacticTarget
from custom_code.tests.helpers import assert_instances_match


class TestAlercePhotometryClient(TransactionTestCase):
    def test_should_fetch_photometry_and_convert_to_candidates(
        self,
    ):

        SURVEY = "ztf"
        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
        ]

        EXPECTED_RESULTS = [
            PhotometryCandidate(
                20.329191,
                "ZTF_g",
                0.27630877,
                "ZTF21abasvhl",
                datetime.datetime(
                    2025, 11, 23, 12, 54, 20, 1589, tzinfo=TimezoneInfo()
                ),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.972315,
                "ZTF_r",
                0.2417613,
                "ZTF21abasvhl",
                datetime.datetime(2025, 11, 26, 11, 50, 0, 3858, tzinfo=TimezoneInfo()),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.954105,
                "ZTF_r",
                0.2373396,
                "ZTF21abasvhl",
                datetime.datetime(2025, 12, 13, 11, 48, 30, 966, tzinfo=TimezoneInfo()),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.831471089064905,
                "ZTF_r",
                0.10057333271756115,
                "ZTF21abasvhl",
                datetime.datetime(2025, 12, 11, 11, 51, 27, 6, tzinfo=TimezoneInfo()),
                "ALERCE",
            ),
            PhotometryCandidate(
                20.309108461379605,
                "ZTF_g",
                0.26643242359717245,
                "ZTF21abasvhl",
                datetime.datetime(2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.755860335859563,
                "ZTF_r",
                0.21424798385515845,
                "ZTF21abasvhl",
                datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                "ALERCE",
            ),
        ]

        with mock.patch(
            "custom_code.photometry.AlercePhotometryClient.Alerce"
        ) as mocked:
            data_folder = path.join("custom_code", "tests", "mocks", "responses")
            # GIVEN mock implementation for Alerce query_detections
            def replacement_detections(*args, **kwargs):
                name = args[0]
                ALERCE_QUERY_DETECTIONS_PICKLE = path.join(data_folder, f"alerce__query_detections__{name}.pkl")
                with open(ALERCE_QUERY_DETECTIONS_PICKLE, "rb") as f:
                    result = pickle.load(f)
                return result[:3]

            # GIVEN mock implementation for Alerce query_forced_photometry
            def replacement_forced(*args, **kwargs):
                name = args[0]
                ALERCE_QUERY_FORCED_PICKLE = path.join(
                    data_folder, f"alerce__query_forced_photometry__{name}.pkl"
                )
                with open(ALERCE_QUERY_FORCED_PICKLE, "rb") as f:
                    result = pickle.load(f)
                return result[:3]

            instance = mocked.return_value
            instance.query_detections.side_effect = replacement_detections
            instance.query_forced_photometry.side_effect = replacement_forced

            alerce_photometry_client = AlercePhotometryClient()

            # WHEN the testee is called
            actual_result = alerce_photometry_client.fetch_photometry_for_targets(
                TARGETS, survey=SURVEY
            )
            PHOT_FIELDS = [
                "magnitude",
                "filter",
                "error",
                "location",
                "timestamp",
                "source",
            ]

            # THEN the expcted results should be returned
            assert_instances_match(
                EXPECTED_RESULTS, actual_result, PHOT_FIELDS, "timestamp"
            )
            # AND the third party API should called correctly
            for i, call_args in enumerate(instance.query_detections.call_args_list):
                target = TARGETS[i]
                name = target.name
                self.assertEqual(call_args.args[0], name)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)
            for i, call_args in enumerate(
                instance.query_forced_photometry.call_args_list
            ):
                target = TARGETS[i]
                name = target.name
                self.assertEqual(call_args.args[0], name)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)

    def test_should_return_empty_list_on_no_results(
        self,
    ):

        SURVEY = "ztf"
        TARGETS = [
            GalacticTarget(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
        ]

        EXPECTED_RESULTS = []

        with mock.patch(
            "custom_code.photometry.AlercePhotometryClient.Alerce"
        ) as mocked:
            # GIVEN mock implementation for Alerce query_detections
            def replacement_detections(*args, **kwargs):
                return pd.DataFrame([])

            # GIVEN mock implementation for Alerce query_forced_photometry
            def replacement_forced(*args, **kwargs):
                return pd.DataFrame([])

            instance = mocked.return_value
            instance.query_detections.side_effect = replacement_detections
            instance.query_forced_photometry.side_effect = replacement_forced

            alerce_photometry_client = AlercePhotometryClient()

            # WHEN the testee is called
            actual_result = alerce_photometry_client.fetch_photometry_for_targets(
                TARGETS, survey=SURVEY
            )

            # THEN the expcted results should be returned
            self.assertListEqual(actual_result, EXPECTED_RESULTS)
            # AND the third party API should called correctly
            for i, call_args in enumerate(instance.query_detections.call_args_list):
                target = TARGETS[i]
                name = target.name
                self.assertEqual(call_args.args[0], name)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)
            for i, call_args in enumerate(
                instance.query_forced_photometry.call_args_list
            ):
                target = TARGETS[i]
                name = target.name
                self.assertEqual(call_args.args[0], name)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)
