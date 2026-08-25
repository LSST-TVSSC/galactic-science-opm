import datetime
from unittest import mock

from django.db import IntegrityError

from astropy.time import TimezoneInfo
from django.test import TransactionTestCase
from tom_dataproducts.models import PhotometryReducedDatum
from tom_targets.models import Target

from custom_code.photometry.PhotometryApiClient import PhotometryCandidate
from custom_code.photometry.PhotometryCreator import PhotometryCreator
from custom_code.tests.helpers import (
    assert_instances_match,
    create_raising_create_or_update,
    make_exception_to_be_raised,
)


class TestPhotometryCreator(TransactionTestCase):
    def test_should_create_photometry_reduced_datums_from_candidates(self):
        PHOTOMETRY_CANDIDATES = [
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

        target_ZTF21abasvhl = Target.objects.create(name="ZTF21abasvhl")
        EXPECTED_DATUMS = [
            PhotometryReducedDatum.objects.create(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF21abasvhl",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF21abasvhl,
            ),
            PhotometryReducedDatum.objects.create(
                brightness=19.755860335859563,
                bandpass="ZTF_r",
                brightness_error=0.21424798385515845,
                source_location="ZTF21abasvhl",
                timestamp=datetime.datetime(
                    2025, 12, 5, 12, 51, 24, 998395, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF21abasvhl,
            ),
        ]

        # GIVEN a 'regular' instance of all involved entities
        photometry_creator = PhotometryCreator()
        # WHEN testee is called
        errors, results = photometry_creator.create_photometry_for_targets(
            PHOTOMETRY_CANDIDATES
        )

        PHOT_FIELDS = [
            "brightness",
            "bandpass",
            "brightness_error",
            "source_location",
            "timestamp",
            "source_name",
            # mkistner: it seems tomtk uses BaseTarget here, not Target, so 
            # I can't compare them here and have to do it separately.
            # "target", 
        ]

        # It should create PhotometryReducedDatum instances from candidates in the DB
        assert_instances_match(EXPECTED_DATUMS, results, PHOT_FIELDS, "timestamp")
        self.assertEqual(len(errors), 0)
        for e in EXPECTED_DATUMS:
            self.assertEqual(e.target.name, target_ZTF21abasvhl.name)

    def test_should_return_exceptions_during_creation(self):
        PHOTOMETRY_CANDIDATES = [
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

        target_ZTF21abasvhl = Target.objects.create(name="ZTF21abasvhl")
        EXPECTED_DATUMS = [
            PhotometryReducedDatum.objects.create(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF21abasvhl",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF21abasvhl,
            ),
        ]
        
        expected_error_message = ('ALERCE HARVERSTER: Exception occured while ingesting photometry')
        expected_error_message += ('Exception')
        expected_error_message += 'oops'
        EXPECTED_ERRORS = [{"message": expected_error_message, "target":target_ZTF21abasvhl.name}]


        # GIVEN a PhotometryReducedDatum implementation which raises an exception
        # on create_or_update
        with mock.patch(
            "custom_code.photometry.PhotometryCreator.PhotometryReducedDatum",
            new_callable=create_raising_create_or_update(
                EXPECTED_DATUMS,
                make_exception_to_be_raised(Exception, "oops")
            )
        ):
            photometry_creator = PhotometryCreator()
            # WHEN testee is run
            errors, results = photometry_creator.create_photometry_for_targets(
                PHOTOMETRY_CANDIDATES
            )

            PHOT_FIELDS = [
                "brightness",
                "bandpass",
                "brightness_error",
                "source_location",
                "timestamp",
                "source_name",
                # "target", # mkistner: it seems tomtk uses BaseTarget here, not Target
            ]

            # THEN PhotometryReducedDatum instances should be present in DB where possible
            assert_instances_match(EXPECTED_DATUMS, results, PHOT_FIELDS, "timestamp")
            for e in EXPECTED_DATUMS:
                self.assertEqual(e.target.name, target_ZTF21abasvhl.name)
            # AND errors should be saved
            self.assertListEqual(errors, EXPECTED_ERRORS)

    def test_should_ignore_integrity_error_for_phot(self):
        PHOTOMETRY_CANDIDATES = [
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

        target_ZTF21abasvhl = Target.objects.create(name="ZTF21abasvhl")
        EXPECTED_DATUMS = [
            PhotometryReducedDatum.objects.create(
                brightness=20.309108461379605,
                bandpass="ZTF_g",
                brightness_error=0.26643242359717245,
                source_location="ZTF21abasvhl",
                timestamp=datetime.datetime(
                    2025, 12, 7, 12, 46, 46, 4173, tzinfo=TimezoneInfo()
                ),
                source_name="ALERCE",
                target=target_ZTF21abasvhl,
            ),
        ]


        # GIVEN a PhotometryReducedDatum implementation that raises an 
        # IntegrityError on create_or_update
        with mock.patch(
            "custom_code.photometry.PhotometryCreator.PhotometryReducedDatum",
            new_callable=create_raising_create_or_update(
                EXPECTED_DATUMS,
                make_exception_to_be_raised(IntegrityError, "unique_photometry"),
            ),
        ):
            photometry_creator = PhotometryCreator()
            # WHEN testee is called 
            errors, results = photometry_creator.create_photometry_for_targets(
                PHOTOMETRY_CANDIDATES
            )

            PHOT_FIELDS = [
                "brightness",
                "bandpass",
                "brightness_error",
                "source_location",
                "timestamp",
                "source_name",
                # "target", # mkistner: it seems tomtk uses BaseTarget here, not Target
            ]

            # THEN all PhotometryReducedDatum instances should be created
            assert_instances_match(EXPECTED_DATUMS, results, PHOT_FIELDS, "timestamp")
            for e in EXPECTED_DATUMS:
                self.assertEqual(e.target.name, target_ZTF21abasvhl.name)
            # AND no errors should be logged, since IntegrityError regarding
            # unique_photometry are ok. 
            self.assertEqual(len(errors), 0)
