from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from custom_code.target_models import GalacticTarget, MicrolensingRadarData
from custom_code.utils.vizier_sed import (
    VIZIER_SED_DEFAULT_RADIUS_ARCSEC,
    VIZIER_SED_DEFAULT_TIMEOUT,
    fetch_and_store_vizier_sed,
    get_latest_stored_vizier_sed,
)


def _recent_and_priority_targets(event_name, recent_days, priority_limit):
    event_name = str(event_name)

    if event_name not in {"ZTF", "LSST"}:
        return list(GalacticTarget.objects.filter(name__icontains=event_name).distinct())

    time_window = timezone.now() - timedelta(days=recent_days)

    new_or_modified_targets = (
        GalacticTarget.objects.filter(
            Q(modified__gte=time_window)
            | Q(reduceddatum__timestamp__gte=time_window)
        )
        .filter(name__icontains=event_name)
        .filter(known_variability__icontains="queried")
        .distinct()
    )

    if event_name == "LSST":
        radar_qs = (
            MicrolensingRadarData.objects.filter(target__name__icontains=event_name)
            .distinct()
        )
    else:
        distinct_ids = (
            MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
            .distinct("target_id")
            .filter(target__name__icontains=event_name)
            .filter(average_master_probability__gt=0.0)
            .filter(target__known_variability__icontains="queried")
        )
        radar_qs = (
            MicrolensingRadarData.objects.filter(
                id__in=distinct_ids,
                target_id__isnull=False,
            )
            .order_by("-average_master_probability")
            .distinct()[:priority_limit]
        )

    target_ids = set(new_or_modified_targets.values_list("id", flat=True))
    target_ids.update(
        radar_qs.values_list("target_id", flat=True)
    )

    return list(GalacticTarget.objects.filter(id__in=target_ids).distinct())


class Command(BaseCommand):
    help = "Fetch and store VizieR SED data for recent and high-priority microlensing targets."

    def add_arguments(self, parser):
        parser.add_argument(
            "event",
            nargs="?",
            default="ZTF",
            help="Event-name filter. Use ZTF or LSST for recent/priority target selection.",
        )
        parser.add_argument("--radius-arcsec", type=float, default=VIZIER_SED_DEFAULT_RADIUS_ARCSEC)
        parser.add_argument("--timeout", type=float, default=VIZIER_SED_DEFAULT_TIMEOUT)
        parser.add_argument("--recent-days", type=int, default=3)
        parser.add_argument("--priority-limit", type=int, default=35)
        parser.add_argument("--max-age-hours", type=float, default=24.0)
        parser.add_argument("--force", action="store_true")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        targets = _recent_and_priority_targets(
            options["event"],
            options["recent_days"],
            options["priority_limit"],
        )

        self.stdout.write(f"Found {len(targets)} targets for VizieR SED population.")
        freshness_cutoff = timezone.now() - timedelta(hours=options["max_age_hours"])

        for target in targets:
            existing_sed = get_latest_stored_vizier_sed(target)

            if (
                existing_sed is not None
                and not options["force"]
                and existing_sed.timestamp >= freshness_cutoff
            ):
                self.stdout.write(f"Skipping {target.name}: stored SED is recent.")
                continue

            self.stdout.write(f"Querying VizieR SED for {target.name}.")

            if options["dry_run"]:
                continue

            _, created, payload = fetch_and_store_vizier_sed(
                target,
                radius_arcsec=options["radius_arcsec"],
                timeout=options["timeout"],
            )

            if payload.get("error"):
                self.stdout.write(
                    self.style.WARNING(
                        f"Stored VizieR SED error for {target.name}: {payload['error']}"
                    )
                )
            else:
                action = "Created" if created else "Updated"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{action} stored VizieR SED for {target.name}: {payload['n_points']} points."
                    )
                )
