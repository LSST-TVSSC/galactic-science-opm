from django.contrib import admin

from .target_models import (
    Classification,
    ClassificationGeneralized,
    ClassificationSource,
    MicrolensingModel,
    MicrolensingRadarData,
)

admin.site.register(MicrolensingModel)
admin.site.register(MicrolensingRadarData)
admin.site.register(Classification)
admin.site.register(ClassificationGeneralized)
admin.site.register(ClassificationSource)
