from django import template
from django.core.exceptions import ObjectDoesNotExist
from custom_code.target_models import Classification, MicrolensingParameterModel
from custom_code.target_models import MicrolensingRadarData


register = template.Library()

@register.filter
def microlensing_parameters_by_name(name):
    try:
        return MicrolensingParameterModel.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None

@register.filter
def microlensing_radar_by_name(name):
    try:
        return MicrolensingRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None

@register.filter
def classification_by_name(name):
    try:
        return Classification.objects.get(target=name).latest()
    except ObjectDoesNotExist:
        return None
