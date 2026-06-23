
from django.contrib import admin
from .target_models import ClassificationGeneralized, ClassificationSource, MicrolensingModel
from .target_models import MicrolensingRadarData
from .target_models import Classification

admin.site.register(MicrolensingModel)
admin.site.register(MicrolensingRadarData)
admin.site.register(Classification)
admin.site.register(ClassificationGeneralized)
admin.site.register(ClassificationSource)
