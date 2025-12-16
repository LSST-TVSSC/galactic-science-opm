from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification
from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
from os import path

def microlensing_model_view(request):
    microlensing_models = MicrolensingModel.objects.all()  # Get all MicrolensingModels
    try:
        return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})
    
def microlensing_prob_view(request):
    microlensing_objects = Classification.objects.order_by("-prob_class1")
    try:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})


class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Very simple first pass: just take the 7 most probable
        # (we know they at least have id and name).
        # This can be modifed with any selector function later.
        # First modification: prob_class1
        target_ids = Classification.objects.all().order_by("-prob_class1").values_list('target_id', flat=True).distinct()[:11]
        target_objects = GalacticTarget.objects.filter(id__in=target_ids)
        featured = (target_objects)
        context["featured_targets"] = featured
        return context

