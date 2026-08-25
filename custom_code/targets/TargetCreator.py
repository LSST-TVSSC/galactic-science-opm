from custom_code.match_managers import validators
from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG


class TargetCreator:
    def create_targets_from_candidates(self, candidates):
        total_targets = []
        new_targets = []
        for candidate in candidates:
            target, result = validators.get_or_create_event(
                candidate["name"], candidate["ra"], candidate["dec"]
            )
            if result == "new_target":
                new_targets.append(target)

            total_targets.append(target)
        return total_targets, new_targets

    def make_targets_public(self, targets):
        for target in targets:
            target.permissions = GalacticTarget.Permissions.PUBLIC
            target.save()

    def update_known_extragalactic(self, targets, extragalactic_info):
        for target in targets:
            count = extragalactic_info[target.name]["count"]
            success = extragalactic_info[target.name]["success"]
            if not success:
                continue

            if count > 0:
                target.known_extragalactic = GalacticTarget.CatalogFlag.IN_GLADE_PLUS
            else:
                target.known_extragalactic = (
                    GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS
                )
            target.save()

    def update_expected_visits(self, targets, visits_info):
        for target in targets:
            target.expected_visits = visits_info[target.name]["visits"]
            target.save()

    def update_known_variability(self, targets, variability_info):
        for target in targets:
            flags = variability_info[target.name]["flags"]
            success = variability_info[target.name]["success"]

            if not success:
                continue
            if len(flags) == 0:
                target.known_variability = NOT_IN_ANY_CATALOG
            else:
                target.known_variability = ",".join(variability_info[target.name]["flags"])
            target.save()

    def get_priority_targets(self, amount_of_targets, survey):

        distinct_ids = (
            MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
            .distinct("target_id")
            .filter(target__name__icontains=survey)
            .filter(average_master_probability__gt=0.0)
        )
        qs = (
            MicrolensingRadarData.objects.filter(id__in=distinct_ids)
            .order_by("-average_master_probability")
            .distinct()[:amount_of_targets]
        )
        priority_targets = [
            GalacticTarget.objects.filter(name__icontains=target.target.name).last()
            for target in qs
        ]
        return priority_targets
