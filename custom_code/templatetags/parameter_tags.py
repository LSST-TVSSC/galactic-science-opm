from django import template
from django.core.exceptions import ObjectDoesNotExist
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification

register = template.Library()

@register.filter
def microlensing_parameters_by_name(name):
    try:
        return MicrolensingModel.objects.get(target=name)
    except ObjectDoesNotExist:
        return None

@register.filter
def classification_by_name(name):
    try:
        return Classification.objects.get(target=name)
    except ObjectDoesNotExist:
        return None