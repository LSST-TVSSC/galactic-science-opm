from os import path
import os
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from custom_code.target_models import (
    GalacticTarget,
    MicrolensingModel,
    MicrolensingStatisticalModel,
    StatisticalModelImage,
)


class Command(BaseCommand):
    help = "Migrates existing MicrolensingModel to MicrolensingStatisticalModel"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        existing_targets = GalacticTarget.objects.all()

        for target in existing_targets:

            if target.statistical_models.count() > 0:
                self.stdout.write(self.style.NOTICE(f"Target {target.name} already has statistical_models. Skipping."))
                continue

            microlensing_models_for_target = MicrolensingModel.objects.filter(target=target)
            if not microlensing_models_for_target.exists():
                self.stdout.write(self.style.NOTICE(f"Target {target.name} has no MicrolensingModel instances. Skipping."))
                continue

            latest_model = microlensing_models_for_target.latest()

            path_to_current_image = path.join(settings.MEDIA_ROOT, f"{target.name}.png")  
            ml_model = MicrolensingStatisticalModel.objects.create(
                target=target,
                u0=latest_model.u0,
                t0=latest_model.t0,
                tE=latest_model.tE,
                err_u0=latest_model.err_u0,
                err_t0=latest_model.err_t0,
                err_tE=latest_model.err_tE,
                err_rho=latest_model.err_rho,
                rho=latest_model.rho,
            )

            image_path = Path(path_to_current_image)
            if path.exists(image_path):
                with image_path.open(mode="rb") as f:
                    image = File(f, name=image_path.name)
                    StatisticalModelImage.objects.create(
                        statistical_model=ml_model, image=image
                    )
                    # Do not remove the image for now.
                    #os.remove(path_to_current_image)
                    self.stdout.write(self.style.SUCCESS(f"Migrated model and image for target {target.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Migrated model {target.name}, could not find image."))

