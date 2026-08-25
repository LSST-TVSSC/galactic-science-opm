import pickle
from unittest import mock

from alerce.core import Alerce
from astropy.time import Time
from django.test import TransactionTestCase

from custom_code.targets.AlerceApiClient import AlerceApiClient
from custom_code.tests.mocks.responses.alerce_api_client_results import EXPECTED_DATA
from custom_code.tests.mocks.external.AlerceMock import AlerceMock


# python manage.py test custom_code.tests.unit.targets.AlerceApiClient --settings=galactic_science_opm.settings_test
class TestAlerceApiClient(TransactionTestCase):
    def test_should_convert_alerce_results_to_candidate_list(self):
        START_DATE = 61248.0
        SURVEY = "ztf"
        CLASS_NAME = "Microlensing"
        DAYS = 2

        # GIVEN an Alerce implementation that serves 3 pages of valid results
        # and a pagesize of 10
        STEP = 10
        PAGES = 3
        replacement = AlerceMock()
        replacement.step = STEP
        replacement.pages = PAGES

        with mock.patch(
            "custom_code.targets.AlerceApiClient.Alerce",
        ) as mocked:
            instance = mocked.return_value
            instance.query_objects.side_effect = replacement.query_objects

            alerce_api_client = AlerceApiClient()
            # WHEN the testee is called
            actual_result = alerce_api_client.fetch_potential_targets(
                survey=SURVEY,
                class_name=CLASS_NAME,
                since_n_days=DAYS,
                start_date=START_DATE,
            )
            # THEN the results should match the expected results
            self.assertEquals(actual_result, EXPECTED_DATA)
            # AND the third party API should be called correctly
            self.assertEqual(len(instance.query_objects.call_args_list), PAGES + 1)
            for i, call_args in enumerate(instance.query_objects.call_args_list):
                self.assertEqual(
                    call_args.kwargs["classifier"], "lc_classifier_BHRF_forced_phot"
                )
                self.assertEqual(call_args.kwargs["class_name"], CLASS_NAME)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["firstmjd"], START_DATE - DAYS)
                self.assertEqual(call_args.kwargs["page"], i + 1)
                self.assertEqual(call_args.kwargs["order_by"], "probability")
                self.assertEqual(call_args.kwargs["order_mode"], "DESC")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)

    def test_should_return_empty_list_if_no_results(self):
        START_DATE = 61248.0
        SURVEY = "ztf"
        CLASS_NAME = "Microlensing"
        DAYS = 2
        PAGES = 0

        # GIVEN a Alerce implementation with no results
        STEP = 10
        replacement = AlerceMock()
        replacement.step = STEP
        replacement.pages = PAGES

        with mock.patch(
            "custom_code.targets.AlerceApiClient.Alerce",
        ) as mocked:
            instance = mocked.return_value
            instance.query_objects.side_effect = replacement.query_objects
            alerce_api_client = AlerceApiClient()

            # WHEN testee is called
            actual_result = alerce_api_client.fetch_potential_targets(
                survey=SURVEY,
                class_name=CLASS_NAME,
                since_n_days=DAYS,
                start_date=START_DATE,
            )
            # THEN the correct results should be returned
            self.assertEquals(actual_result, [])
            # AND the third party API should be called correctly
            for i, call_args in enumerate(instance.query_objects.call_args_list):
                self.assertEqual(
                    call_args.kwargs["classifier"], "lc_classifier_BHRF_forced_phot"
                )
                self.assertEqual(call_args.kwargs["class_name"], CLASS_NAME)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                self.assertEqual(call_args.kwargs["firstmjd"], START_DATE - DAYS)
                self.assertEqual(call_args.kwargs["page"], i + 1)
                self.assertEqual(call_args.kwargs["order_by"], "probability")
                self.assertEqual(call_args.kwargs["order_mode"], "DESC")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)

    def test_should_use_current_date_if_nothing_provided(self):
        START_DATE = None
        SURVEY = "ztf"
        CLASS_NAME = "Microlensing"
        DAYS = 2
        STEP = 10
        PAGES = 0

        replacement = AlerceMock()
        replacement.step = STEP
        replacement.pages = PAGES

        with mock.patch(
            "custom_code.targets.AlerceApiClient.Alerce",
        ) as mocked:
            instance = mocked.return_value
            instance.query_objects.side_effect = replacement.query_objects

            # GIVEN a testee
            alerce_api_client = AlerceApiClient()
            # WHEN testee is called with no date
            actual_result = alerce_api_client.fetch_potential_targets(
                survey=SURVEY,
                class_name=CLASS_NAME,
                since_n_days=DAYS,
                start_date=START_DATE,
            )
            self.assertEquals(actual_result, [])
            now = int(Time.now().mjd)
            for i, call_args in enumerate(instance.query_objects.call_args_list):
                self.assertEqual(
                    call_args.kwargs["classifier"], "lc_classifier_BHRF_forced_phot"
                )

                self.assertEqual(call_args.kwargs["class_name"], CLASS_NAME)
                self.assertEqual(call_args.kwargs["format"], "pandas")
                # THEN it should call the third party API with an offset based on current date
                self.assertEqual(call_args.kwargs["firstmjd"], now - DAYS)
                self.assertEqual(call_args.kwargs["page"], i + 1)
                self.assertEqual(call_args.kwargs["order_by"], "probability")
                self.assertEqual(call_args.kwargs["order_mode"], "DESC")
                self.assertEqual(call_args.kwargs["survey"], SURVEY)

    def generate_alerce_data(self):
        class_name = "Microlensing"
        alerce = Alerce()
        start_date = int(Time.now().mjd)
        days = 1
        survey = "ztf"

        _ = alerce.query_objects(
            classifier="lc_classifier_BHRF_forced_phot",
            class_name=class_name,
            format="pandas",
            firstmjd=float(start_date - days),
            order_by="probability",
            order_mode="DESC",
            page_size=50,
            survey=survey,
        )

    def generate_targets_for_cv_nova(self):
        alerce_api_client = AlerceApiClient()
        alerce_api_client.generate_alerce_data("CV/Nova")

        VIZIER_QUERY_REGION_PICKLE = "alerce__query_objects_CVNova_61282.pkl"
        with open(VIZIER_QUERY_REGION_PICKLE, "rb") as f:
            result = pickle.load(f)
        print([(t["oid"], t["meanra"], t["meandec"]) for _, t in result[:3].iterrows()])
