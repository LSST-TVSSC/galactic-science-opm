from django import template
from django.core.exceptions import ObjectDoesNotExist

from custom_code.target_models import (
    CompactBinariesRadarData,
    GalacticTarget,
    MicrolensingParameterModel,
    MicrolensingRadarData,
)

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
def compact_binaries_radar_by_name(name):
    try:
        return CompactBinariesRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None


@register.filter
def radardata_by_name(name):
    try:
        target = GalacticTarget.objects.get(name=name)
        if target.target_type == "Microlensing candidate":
            return MicrolensingRadarData.objects.filter(target=name).latest()
        elif target.target_type == "CV/Nova candidate":
            return CompactBinariesRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None
