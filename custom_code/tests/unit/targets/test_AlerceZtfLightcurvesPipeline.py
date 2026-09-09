import datetime
from astropy.time import Time, TimezoneInfo

from django.test import TransactionTestCase
from custom_code.targets.AlerceZtfLightcurvesPipeline import (
    AlerceZtfLightcurvesPipeline,
)
from tom_dataproducts.models import PhotometryReducedDatum
from tom_targets.models import BaseTarget

from custom_code.catalogs.ExtragalacticInfoApiClient import ExtragalacticInfoApi
from custom_code.observations.ExpectedVisitsApiClient import ExpectedVisitsApiClient
from custom_code.photometry.PhotometryApiClient import (
    PhotometryApiClient,
    PhotometryCandidate,
)
from custom_code.photometry.PhotometryCreator import PhotometryCreator
from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.targets.TargetApiClient import TargetApiClient
from custom_code.targets.TargetCreator import TargetCreator
from custom_code.tests.helpers import assert_instances_match
from custom_code.variability.VariabilityFlagsClient import VariabilityFlagsClient

def logger(style, message):
    pass

# These are all mocks for the test
class MockTargetApiClient(TargetApiClient):
    def fetch_potential_targets(self, class_name, survey, start_date, since_n_days):
        target_candidates = []
        if class_name == "Microlensing":
            target_candidates = [
                {
                    "name": "ZTF26abdwauc",
                    "ra": 285.90945662498603,
                    "dec": -25.534577312499998,
                    "known_aliases": [],
                    "lightcurve": [],
                    "survey": "ztf",
                },
                {
                    "name": "ZTF20adjbbvq",
                    "ra": 282.18004242953185,
                    "dec": 0.1652681584040193,
                    "known_aliases": [],
                    "lightcurve": [],
                    "survey": "ztf",
                },
            ]
        elif class_name == "CV/Nova":
            target_candidates = [
                {
                    "name": "ZTF26abeziup",  # cv nova
                    "ra": 294.43367369926995,
                    "dec": -5.595282354767369,
                    "known_aliases": [],
                    "lightcurve": [],
                    "survey": "ztf",
                }
            ]
        return target_candidates


class MockGladeApiClient(ExtragalacticInfoApi):
    def check_glade_plus_for_targets(self, targets):

        info = {
            "ZTF26abdwauc": {
                "success": True,
                "count": 42,
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "count": 42,
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "count": 42,
                "name": "ZTF26abeziup",
            },
        }
        return info


class MockExpectedVisitsApiClient(ExpectedVisitsApiClient):
    def get_expected_visits_for_targets(self, targets):

        info = {
            "ZTF26abdwauc": {
                "success": True,
                "visits": 42,
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "visits": 42,
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "visits": 42,
                "name": "ZTF26abeziup",
            },
        }
        return info


class MockVariabilityFlagsClient(VariabilityFlagsClient):
    def get_variability_info_for_targets(self, targets):

        info = {
            "ZTF26abdwauc": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF26abdwauc",
            },
            "ZTF20adjbbvq": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF20adjbbvq",
            },
            "ZTF26abeziup": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF26abeziup",
            },
        }
        return info


class MockPhotometryApiClient(PhotometryApiClient):
    def __init__(self):
        self.call_counter = 0

    def fetch_photometry_for_targets(self, targets, survey):
        PHOTOMETRY_CANDIDATES = [
            PhotometryCandidate(
                20.309108461379605,
                "ZTF_g",
                0.26643242359717245,
                "ZTF26abdwauc",
                datetime.datetime(2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.755860335859563,
                "ZTF_r",
                0.21424798385515845,
                "ZTF20adjbbvq",
                datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.755860335859563,
                "ZTF_r",
                0.21424798385515845,
                "ztffoo",
                datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                "ALERCE",
            ),
            PhotometryCandidate(
                19.755860335859563,
                "ZTF_r",
                0.21424798385515845,
                "ZTF26abeziup",
                datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                "ALERCE",
            ),
        ]
        results = []
        for target in targets:
            result = [t for t in PHOTOMETRY_CANDIDATES if t.location == target.name]
            if len(result) > 0:
                results.append(result[0])
        return results


class TestTargetCreationPipeline(TransactionTestCase):
    def test_should_run_complete_alerce_ztf_lightcurve_pipeline(self):

        mock_target_api_client = MockTargetApiClient()
        mock_glade_api_client = MockGladeApiClient()
        mock_visits_api_client = MockExpectedVisitsApiClient()
        mock_variability_flags_api_client = MockVariabilityFlagsClient()
        mock_photometry_api_client = MockPhotometryApiClient()

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=mock_target_api_client,
            target_creator=TargetCreator(),
            glade_api_client=mock_glade_api_client,
            visits_checker=mock_visits_api_client,
            variability_checker=mock_variability_flags_api_client,
            photometry_fetcher=mock_photometry_api_client,
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        # GIVEN an existing prio target
        prio_target = GalacticTarget.objects.create(name="ztffoo")
        _ = MicrolensingRadarData.objects.create(
            target=prio_target, average_master_probability=0.9
        )

        # WHEN the pipeline runs
        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey="ztf",
            start_date=int(Time.now().mjd),
            since_n_days=2,
            fetch_photometry_for_all_targets=False,
        )

        all_targets = GalacticTarget.objects.all()
        EXPECTED_TARGETS = [prio_target] + [
            GalacticTarget(
                name="ZTF26abdwauc",
                ra=285.90945662498603,
                dec=-25.534577312499998,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF20adjbbvq",
                ra=282.18004242953185,
                dec=0.1652681584040193,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            # cv nova
            GalacticTarget(
                name="ZTF26abeziup",
                ra=294.43367369926995,
                dec=-5.595282354767369,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
        ]

        FIELDS_TO_CHECK = [
            "name",
            "dec",
            "ra",
            "known_variability",
            "known_extragalactic",
            "permissions",
            "expected_visits",
        ]

        # THEN all existing and expedted targets should be in the database
        # AND should be public
        # AND should have variability info set
        # AND should have extragalactic info set
        # AND should have expected_visits set
        assert_instances_match(EXPECTED_TARGETS, all_targets, FIELDS_TO_CHECK, "name")

        all_phot = PhotometryReducedDatum.objects.all()
        target_ZTF26abdwauc = BaseTarget.objects.get(name="ZTF26abdwauc")
        target_ZTF20adjbbvq = BaseTarget.objects.get(name="ZTF20adjbbvq")
        target_foo = BaseTarget.objects.get(name="ztffoo")
        target_ZTF26abeziup = BaseTarget.objects.get(name="ZTF26abeziup")
        
        EXPECTED_DATUMS = [
            PhotometryReducedDatum(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF26abdwauc",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abdwauc,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF20adjbbvq",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF20adjbbvq,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ztffoo",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_foo,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF26abeziup",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abeziup,
            ),
        ]

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            "target",
        ]

        # AND all PhotometryReducedDatums should be correctly created
        assert_instances_match(
            EXPECTED_DATUMS, all_phot, PHOT_FIELDS, "source_location"
        )

    def test_should_run_complete_alerce_ztf_lightcurve_pipeline_and_respect_full_phot_true(
        self,
    ):

        mock_target_api_client = MockTargetApiClient()
        mock_glade_api_client = MockGladeApiClient()
        mock_visits_api_client = MockExpectedVisitsApiClient()
        mock_variability_flags_api_client = MockVariabilityFlagsClient()
        mock_photometry_api_client = MockPhotometryApiClient()

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=mock_target_api_client,
            target_creator=TargetCreator(),
            glade_api_client=mock_glade_api_client,
            visits_checker=mock_visits_api_client,
            variability_checker=mock_variability_flags_api_client,
            photometry_fetcher=mock_photometry_api_client,
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        # GIVEN an existing target
        _ = GalacticTarget.objects.create(
            name="ZTF26abdwauc",
            ra=285.90945662498603,
            dec=-25.534577312499998,
            permissions=GalacticTarget.Permissions.PUBLIC.value,
            known_variability="foo,bar",
            known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
            expected_visits=42,
        )

        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey="ztf",
            start_date=int(Time.now().mjd),
            since_n_days=2,
            fetch_photometry_for_all_targets=True,
        )

        # should create correct targets
        all_targets = GalacticTarget.objects.all()
        EXPECTED_TARGETS = [
            GalacticTarget(
                name="ZTF26abdwauc",
                ra=285.90945662498603,
                dec=-25.534577312499998,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF20adjbbvq",
                ra=282.18004242953185,
                dec=0.1652681584040193,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            # cv nova
            GalacticTarget(
                name="ZTF26abeziup",
                ra=294.43367369926995,
                dec=-5.595282354767369,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
        ]

        FIELDS_TO_CHECK = [
            "name",
            "dec",
            "ra",
            "known_variability",
            "known_extragalactic",
            "permissions",
            "expected_visits",
        ]

        assert_instances_match(EXPECTED_TARGETS, all_targets, FIELDS_TO_CHECK, "name")

        # should create correct photometry
        all_phot = PhotometryReducedDatum.objects.all()
        target_ZTF26abdwauc = BaseTarget.objects.get(name="ZTF26abdwauc")
        target_ZTF20adjbbvq = BaseTarget.objects.get(name="ZTF20adjbbvq")
        target_ZTF26abeziup = BaseTarget.objects.get(name="ZTF26abeziup")
        
        EXPECTED_DATUMS = [
            PhotometryReducedDatum(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF26abdwauc",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abdwauc,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF20adjbbvq",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF20adjbbvq,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF26abeziup",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abeziup,
            ),
        ]

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            "target",
        ]

        assert_instances_match(
            EXPECTED_DATUMS, all_phot, PHOT_FIELDS, "source_location"
        )

    def test_should_run_complete_alerce_ztf_lightcurve_pipeline_and_respect_full_phot_false(
        self,
    ):

        mock_target_api_client = MockTargetApiClient()
        mock_glade_api_client = MockGladeApiClient()
        mock_visits_api_client = MockExpectedVisitsApiClient()
        mock_variability_flags_api_client = MockVariabilityFlagsClient()
        mock_photometry_api_client = MockPhotometryApiClient()

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=mock_target_api_client,
            target_creator=TargetCreator(),
            glade_api_client=mock_glade_api_client,
            visits_checker=mock_visits_api_client,
            variability_checker=mock_variability_flags_api_client,
            photometry_fetcher=mock_photometry_api_client,
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        # GIVEN an existing target with no photometry, yet
        _ = GalacticTarget.objects.create(
            name="ZTF26abdwauc",
            ra=285.90945662498603,
            dec=-25.534577312499998,
            permissions=GalacticTarget.Permissions.PUBLIC.value,
            known_variability="foo,bar",
            known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
            expected_visits=42,
        )

        # WHEN a pipeline runs, which does not request photometry for all targets
        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey="ztf",
            start_date=int(Time.now().mjd),
            since_n_days=2,
            fetch_photometry_for_all_targets=False,
        )

        # THEN all targets should be created with correct attributes
        all_targets = GalacticTarget.objects.all()
        EXPECTED_TARGETS = [
            GalacticTarget(
                name="ZTF26abdwauc",
                ra=285.90945662498603,
                dec=-25.534577312499998,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF20adjbbvq",
                ra=282.18004242953185,
                dec=0.1652681584040193,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF26abeziup",
                ra=294.43367369926995,
                dec=-5.595282354767369,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
        ]

        FIELDS_TO_CHECK = [
            "name",
            "dec",
            "ra",
            "known_variability",
            "known_extragalactic",
            "permissions",
            "expected_visits",
        ]

        assert_instances_match(EXPECTED_TARGETS, all_targets, FIELDS_TO_CHECK, "name")

        # AND all PhotometryReducedDatum should be created, but not the ones for the
        # existing target
        all_phot = PhotometryReducedDatum.objects.all()
        target_ZTF20adjbbvq = BaseTarget.objects.get(name="ZTF20adjbbvq")
        target_ZTF26abeziup = BaseTarget.objects.get(name="ZTF26abeziup")
        EXPECTED_DATUMS = [
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF20adjbbvq",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF20adjbbvq,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF26abeziup",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abeziup,
            ),
        ]

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            "target",
        ]

        assert_instances_match(
            EXPECTED_DATUMS, all_phot, PHOT_FIELDS, "source_location"
        )

    def test_should_run_alerce_ztf_lightcurve_pipeline_but_ignore_existing_non_prio(
        self,
    ):

        mock_target_api_client = MockTargetApiClient()
        mock_glade_api_client = MockGladeApiClient()
        mock_visits_api_client = MockExpectedVisitsApiClient()
        mock_variability_flags_api_client = MockVariabilityFlagsClient()
        mock_photometry_api_client = MockPhotometryApiClient()

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=mock_target_api_client,
            target_creator=TargetCreator(),
            glade_api_client=mock_glade_api_client,
            visits_checker=mock_visits_api_client,
            variability_checker=mock_variability_flags_api_client,
            photometry_fetcher=mock_photometry_api_client,
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        # GIVEN an existing non-prio target
        non_prio_target = GalacticTarget.objects.create(name="ztffoo")
        _ = MicrolensingRadarData.objects.create(
            target=non_prio_target, average_master_probability=0
        )

        # WHEN the pipeline runs
        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey="ztf",
            start_date=int(Time.now().mjd),
            since_n_days=2,
            fetch_photometry_for_all_targets=False,
        )

        # THEN all targets should be created
        all_targets = GalacticTarget.objects.all()
        EXPECTED_TARGETS = [non_prio_target] + [
            GalacticTarget(
                name="ZTF26abdwauc",
                ra=285.90945662498603,
                dec=-25.534577312499998,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF20adjbbvq",
                ra=282.18004242953185,
                dec=0.1652681584040193,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF26abeziup",
                ra=294.43367369926995,
                dec=-5.595282354767369,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
        ]

        FIELDS_TO_CHECK = [
            "name",
            "dec",
            "ra",
            "known_variability",
            "known_extragalactic",
            "permissions",
            "expected_visits",
        ]

        assert_instances_match(EXPECTED_TARGETS, all_targets, FIELDS_TO_CHECK, "name")

        # AND all photometry should be created, but not for the non-prio target
        all_phot = PhotometryReducedDatum.objects.all()
        target_ZTF26abdwauc = BaseTarget.objects.get(name="ZTF26abdwauc")
        target_ZTF20adjbbvq = BaseTarget.objects.get(name="ZTF20adjbbvq")
        target_ZTF26abeziup = BaseTarget.objects.get(name="ZTF26abeziup")
        EXPECTED_DATUMS = [
            PhotometryReducedDatum(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF26abdwauc",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abdwauc,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF20adjbbvq",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF20adjbbvq,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF26abeziup",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abeziup,
            ),
        ]

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            "target",
        ]

        assert_instances_match(
            EXPECTED_DATUMS, all_phot, PHOT_FIELDS, "source_location"
        )

    def test_should_run_complete_alerce_ztf_lightcurve_pipeline_with_event_name_filter(self):

        # GIVEN a target API client that returns a target named 'ZTF20adjbbvq', 
        # i.e. that does not match the filter for ZTF26
        mock_target_api_client = MockTargetApiClient()

        mock_glade_api_client = MockGladeApiClient()
        mock_visits_api_client = MockExpectedVisitsApiClient()
        mock_variability_flags_api_client = MockVariabilityFlagsClient()
        mock_photometry_api_client = MockPhotometryApiClient()

        pipeline = AlerceZtfLightcurvesPipeline(
            target_api_client=mock_target_api_client,
            target_creator=TargetCreator(),
            glade_api_client=mock_glade_api_client,
            visits_checker=mock_visits_api_client,
            variability_checker=mock_variability_flags_api_client,
            photometry_fetcher=mock_photometry_api_client,
            photometry_creator=PhotometryCreator(),
            logger=logger
        )

        # GIVEN an existing target that does not match the event_name filter
        # BUT has a high priority
        prio_target = GalacticTarget.objects.create(name="ztffoo")
        _ = MicrolensingRadarData.objects.create(
            target=prio_target, average_master_probability=0.9
        )

        # WHEN the pipeline runs with the event_name filter for ZTF26
        pipeline.run(
            class_names=("Microlensing", "CV/Nova"),
            survey="ztf",
            start_date=int(Time.now().mjd),
            since_n_days=2,
            fetch_photometry_for_all_targets=False,
            event_name="ZTF26"
        )

        # THEN all targets should exist 
        all_targets = GalacticTarget.objects.all()
        EXPECTED_TARGETS = [prio_target] + [
            GalacticTarget(
                name="ZTF26abdwauc",
                ra=285.90945662498603,
                dec=-25.534577312499998,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            GalacticTarget(
                name="ZTF20adjbbvq",
                ra=282.18004242953185,
                dec=0.1652681584040193,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
            # cv nova
            GalacticTarget(
                name="ZTF26abeziup",
                ra=294.43367369926995,
                dec=-5.595282354767369,
                permissions=GalacticTarget.Permissions.PUBLIC.value,
                known_variability="foo,bar",
                known_extragalactic=GalacticTarget.CatalogFlag.IN_GLADE_PLUS.value,
                expected_visits=42,
            ),
        ]

        FIELDS_TO_CHECK = [
            "name",
            "dec",
            "ra",
            "known_variability",
            "known_extragalactic",
            "permissions",
            "expected_visits",
        ]

        assert_instances_match(EXPECTED_TARGETS, all_targets, FIELDS_TO_CHECK, "name")

        # AND all photometry should be created, including existing prio targets
        # BUT not for ZTF20adjbbvq because of event_name filtering
        all_phot = PhotometryReducedDatum.objects.all()
        target_ZTF26abdwauc = BaseTarget.objects.get(name="ZTF26abdwauc")
        target_foo = BaseTarget.objects.get(name="ztffoo")
        target_ZTF26abeziup = BaseTarget.objects.get(name="ZTF26abeziup")
        
        EXPECTED_DATUMS = [
            PhotometryReducedDatum(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF26abdwauc",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abdwauc,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ztffoo",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_foo,
            ),
            PhotometryReducedDatum(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF26abeziup",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF26abeziup,
            ),
        ]

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            "target",
        ]

        assert_instances_match(
            EXPECTED_DATUMS, all_phot, PHOT_FIELDS, "source_location"
        )

