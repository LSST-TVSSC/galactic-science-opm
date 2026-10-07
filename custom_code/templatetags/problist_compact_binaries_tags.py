from django import template
from django.core.exceptions import ObjectDoesNotExist

from custom_code.target_models import (
    Classification,
    CompactBinariesRadarData,
)

register = template.Library()


@register.filter
def microlensing_radar_by_name(name):
    try:
        return CompactBinariesRadarData.objects.filter(target=name).latest()
    except ObjectDoesNotExist:
        return None


@register.filter
def classification_by_name(name):
    try:
        return Classification.objects.get(target=name).latest()
    except ObjectDoesNotExist:
        return None
