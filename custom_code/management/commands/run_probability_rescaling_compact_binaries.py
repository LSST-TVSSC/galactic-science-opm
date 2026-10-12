import healpy as hp
import numpy as np
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction

from custom_code.target_models import (
    Classification,
    ClassificationGeneralized,
    CompactBinariesRadarData,
    GalacticTarget,
)


class Command(BaseCommand):
    help = "Populate the database with updated master probability based on "

    def add_arguments(self, parser):
        parser.add_argument(
            "target_name_contains",
            help="filter for targets containing ... (e.g. ZTF2X), LSST, OGLE",
        )

    def handle(self, *args, **options):
        qs = GalacticTarget.objects.filter(
            name__icontains=str(options["target_name_contains"])
        )
        target_list = list(set(qs))

        config = apps.get_app_config("custom_code")

        hpx_map = config.nsquare_map
        visit_map = config.nvisits_10yrs_map
        nside = config.nside
        for target in target_list:
            class_versions = (
                ClassificationGeneralized.objects.filter(target_id=target)
                .filter(source__classifier_name="lc_classifier_BHRF_forced_phot")
                .values_list("source__classifier_version", flat=True)
                .distinct()
            )

            if len(class_versions) > 0:
                highest_version = max(
                    class_versions, key=lambda v: [int(x) for x in v.split(".")]
                )

                latest_probabilities = (
                    ClassificationGeneralized.objects.filter(target_id=target)
                    .filter(source__classifier_name="lc_classifier_BHRF_forced_phot")
                    .filter(source__classifier_version=str(highest_version))
                    .order_by("name", "-updated_at")
                    .distinct("name")
                )
                ratio_numerator = 0.0
                ratio_denominator = 0.0
                try:
                    for entry in latest_probabilities:
                        if entry.source.class_name != "CV/Nova":
                            ratio_denominator += float(entry.probability)
                        else:
                            ratio_numerator = float(entry.probability)

                    if ratio_denominator == 0.0:
                        prob_contrast = 1.0
                    else:
                        ratio = ratio_numerator / ratio_denominator
                        prob_contrast = ratio / (1 + ratio)
                except Exception:
                    print("no CV/Nova prob contrast available.")
                    prob_contrast = 0.0
            else:
                prob_contrast = 0.0

            target_classification = Classification.objects.filter(target=target)
            if target.classifications.exists():
                try:
                    prob_bogus = (
                        target_classification.filter(source="ALeRCE_ZTF")
                        .latest()
                        .prob_class3
                    )
                except:
                    prob_bogus = 0
                try:
                    if prob_bogus == 0:
                        latest_probabilities = (
                            ClassificationGeneralized.objects.filter(target_id=target)
                            .filter(
                                source__classifier_name="stamp_classifier_rubin_beta_20260421"
                            )
                            .order_by("name", "-updated_at")
                            .distinct("name")
                        )
                        for entry in latest_probabilities:
                            if entry.source.class_name == "bogus":
                                prob_bogus = float(entry.probability)
                except Exception:
                    print("no bogus available.")

                try:
                    pixel_index = hp.ang2pix(
                        nside, target.ra, target.dec, lonlat=True, nest=True
                    )
                    transformed_prob_nsquare = hpx_map[
                        pixel_index
                    ]  # to be included when rescaled map is available
                except:
                    transformed_prob_nsquare = 0

                try:
                    with transaction.atomic():
                        _m = CompactBinariesRadarData.objects.update_or_create(
                            target=target,
                            metric_nsquare=transformed_prob_nsquare,
                            metric_bogus=prob_bogus,
                            metric_probability_ratio=prob_contrast,
                            average_master_probability=np.mean(
                                [
                                    transformed_prob_nsquare,
                                    prob_contrast,
                                ]
                            ),
                        )
                except:
                    print("Rescaled probabilities failed for " + target.name)
            try:
                with transaction.atomic():
                    filtered_target = GalacticTarget.objects.filter(
                        name__icontains=target
                    )
                    pixel_index = hp.ang2pix(
                        128, target.ra, target.dec, lonlat=True, nest=True
                    )
                    filtered_target.update(expected_visits=visit_map[pixel_index])
            except:
                print("Expected visits failed for " + target.name)

        print("rescaled probabilities created/updated.")
        # Filter for to ranked events and augment with variability information
