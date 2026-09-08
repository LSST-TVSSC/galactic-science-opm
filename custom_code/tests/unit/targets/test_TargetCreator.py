from django.test import TransactionTestCase

from custom_code.target_models import GalacticTarget
from custom_code.targets.TargetCreator import TargetCreator
from custom_code.tests.helpers import assert_instances_match
from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG


class TestTargetCreator(TransactionTestCase):
    def test_should_create_targets_from_candidates(self):

        EXPECTED_TARGETS = [
            GalacticTarget(
                name="ZTF26abdwauc", ra=285.90945662498603, dec=-25.534577312499998
            ),
            GalacticTarget(
                name="ZTF20adjbbvq", ra=282.18004242953185, dec=0.1652681584040193
            ),
            GalacticTarget(
                name="ZTF20adjemqk", ra=273.86610041139755, dec=-13.87038172055615
            ),
        ]
        # GIVEN a list of candidates
        TARGET_CANDIDATES = [
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
            {
                "name": "ZTF20adjemqk",
                "ra": 273.86610041139755,
                "dec": -13.87038172055615,
                "known_aliases": [],
                "lightcurve": [],
                "survey": "ztf",
            },
        ]

        target_creator = TargetCreator()
        # WHEN testee is called 
        all_targets, new_targets = target_creator.create_targets_from_candidates(
            TARGET_CANDIDATES
        )

        FIELDS_TO_CHECK = ["name", "dec", "ra"]

        # THEN correct GalacticTarget instances should be created
        self.assertEqual(len(all_targets), len(TARGET_CANDIDATES))
        self.assertEqual(len(new_targets), len(TARGET_CANDIDATES))
        assert_instances_match(EXPECTED_TARGETS, new_targets, FIELDS_TO_CHECK, "name")
        assert_instances_match(new_targets, all_targets, FIELDS_TO_CHECK, "name")

    def test_should_make_targets_public(self):

        # GIVEN an existing set of GalacticTargets
        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        target_creator = TargetCreator()
        # WHEN testee is called 
        target_creator.make_targets_public(TARGETS)

        # THEN existing targets should be public
        created_targets = GalacticTarget.objects.all()
        for target in created_targets:
            self.assertEqual(target.permissions, GalacticTarget.Permissions.PUBLIC)

    def test_should_update_known_extragalactic_when_results_are_found(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of positive counts regarding extragalactic 
        info = {
            "ZTF21abasvhl": {"success": True, "count": 42, "name": "ZTF21abasvhl"},
            "ZTF19adcrpjd": {"success": True, "count": 42, "name": "ZTF19adcrpjd"},
        }

        target_creator = TargetCreator()
        # WHEN testee is called
        target_creator.update_known_extragalactic(TARGETS, info)

        created_targets = GalacticTarget.objects.all()
        # THEN existing targets should have IN_GLADE_PLUS set
        for target in created_targets:
            self.assertEqual(
                target.known_extragalactic, GalacticTarget.CatalogFlag.IN_GLADE_PLUS
            )

    def test_should_update_known_extragalactic_when_no_results_are_found(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of no counts regarding extragalactic 
        info = {
            "ZTF21abasvhl": {"success": True, "count": 0, "name": "ZTF21abasvhl"},
            "ZTF19adcrpjd": {"success": True, "count": 0, "name": "ZTF19adcrpjd"},
        }

        target_creator = TargetCreator()
        # WHEN testee is called 
        target_creator.update_known_extragalactic(TARGETS, info)

        created_targets = GalacticTarget.objects.all()
        # THEN existing targets should have NOT_IN_GLADE_PLUS set
        for target in created_targets:
            self.assertEqual(
                target.known_extragalactic, GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS
            )

    def test_should_not_update_known_extragalactic_if_query_failed(self):
        """
        @todo: This is how it is currently handled: if we don't receive valid 
        results, the default value is not updated, which is an empty 
        string. Is this correct?
        """

        DEFAULT_VALUE = ''

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of unsuccessful info on extragalactic
        info = {
            "ZTF21abasvhl": {"success": False, "count": 0, "name": "ZTF21abasvhl"},
            "ZTF19adcrpjd": {"success": False, "count": 0, "name": "ZTF19adcrpjd"},
        }

        target_creator = TargetCreator()
        # WHEN testee is called 
        target_creator.update_known_extragalactic(TARGETS, info)

        # THEN existing targets should still have their default value for known_extragalactic
        created_targets = GalacticTarget.objects.all()
        for target in created_targets:
            self.assertEqual(
                target.known_extragalactic, DEFAULT_VALUE)

    def test_should_update_expected_visits(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of positive info regarding expected_visits
        info = {
            "ZTF21abasvhl": {"success": True, "visits": 41, "name": "ZTF21abasvhl"},
            "ZTF19adcrpjd": {"success": True, "visits": 42, "name": "ZTF19adcrpjd"},
        }

        target_creator = TargetCreator()
        # WHEN testee is called 
        target_creator.update_expected_visits(TARGETS, info)

        # THEN existing targets should have the correct number of visits
        created_targets = GalacticTarget.objects.all()
        for i, target in enumerate(created_targets):
            self.assertEqual(target.expected_visits, 41 + i)

    def test_should_update_known_variability(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of successful infos on variability
        info = {
            "ZTF21abasvhl": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF21abasvhl",
            },
            "ZTF19adcrpjd": {
                "success": True,
                "flags": ["foo", "bar"],
                "name": "ZTF19adcrpjd",
            },
        }

        target_creator = TargetCreator()
        # WHEN testee is called
        target_creator.update_known_variability(TARGETS, info)

        # THEN existing targets should have flags comma-separated
        created_targets = GalacticTarget.objects.all()
        for target in created_targets:
            self.assertEqual(target.known_variability, "foo,bar")

    def test_should_set_variablily_to_not_in_any_catalog_if_no_flags(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]

        # GIVEN a list of successful infos on variability
        info = {
            "ZTF21abasvhl": {
                "success": True,
                "flags": [],
                "name": "ZTF21abasvhl",
            },
            "ZTF19adcrpjd": {
                "success": True,
                "flags": [],
                "name": "ZTF19adcrpjd",
            },
        }

        target_creator = TargetCreator()
        # WHEN testee is called
        target_creator.update_known_variability(TARGETS, info)

        # THEN existing targets should have NOT_IN_ANY_CATALOG as value
        created_targets = GalacticTarget.objects.all()
        for target in created_targets:
            self.assertEqual(target.known_variability, NOT_IN_ANY_CATALOG)

    def test_should_leave_variability_if_success_is_false(self):

        TARGETS = [
            GalacticTarget.objects.create(
                name="ZTF21abasvhl", ra=209.84372587578667, dec=47.12126690610595
            ),
            GalacticTarget.objects.create(
                name="ZTF19adcrpjd", ra=292.67285206700393, dec=-19.370104587239602
            ),
        ]
        DEFAULT_VALUE = 'None'

        # GIVEN a list of successful infos on variability
        info = {
            "ZTF21abasvhl": {
                "success": False,
                "flags": [],
                "name": "ZTF21abasvhl",
            },
            "ZTF19adcrpjd": {
                "success": False,
                "flags": [],
                "name": "ZTF19adcrpjd",
            },
        }

        target_creator = TargetCreator()
        # WHEN testee is called
        target_creator.update_known_variability(TARGETS, info)

        # THEN existing targets should keep default value
        created_targets = GalacticTarget.objects.all()
        for target in created_targets:
            self.assertEqual(target.known_variability, DEFAULT_VALUE)
