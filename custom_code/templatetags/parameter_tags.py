from django import template
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification

register = template.Library()

@register.filter
def microlensing_parameters_by_name(name):
    return MicrolensingModel.objects.get(target=name)

@register.filter
def classification_by_name(name):
    return Classification.objects.get(target=name)
