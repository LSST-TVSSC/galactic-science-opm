from django import template
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification

register = template.Library()

@register.simple_tag
def microlensing_parameters_by_name(name):
    return MicrolensingModel.objects.filter(name__iexact=name)

@register.simple_tag
def classification_by_name(name):
    return Classification.objects.filter(name__iexact=name)
