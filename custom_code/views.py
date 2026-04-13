from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from custom_code.target_models import GalacticTarget
from custom_code.target_models import MicrolensingModel
from custom_code.target_models import Classification
from custom_code.target_models import MicrolensingRadarData
from django.db.models import OuterRef, Subquery
from django.views.generic import TemplateView
from django.shortcuts import render, get_object_or_404
import plotly.graph_objects as go
from plotly.offline import plot
from os import path
from itertools import chain


def microlensing_model_view(request):
    microlensing_models = MicrolensingModel.objects.all()[:30]  # Get 30 MicrolensingModels
    try:
        return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/model_list.html', {'microlensing_models': microlensing_models})
    
def microlensing_prob_view(request):
    #so far prob class 1 is microlensing, but the model permits other options, to be filtered.

    distinct_ids = Classification.objects.order_by('target_id', '-updated_at').distinct('target_id')
    microlensing_objects_class1 = Classification.objects.filter(id__in=distinct_ids).order_by('-prob_class1').filter(prob_class1__gt=0.)
   
    try:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects_class1': microlensing_objects_class1})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects_class1': microlensing_objects_class1})

def microlensing_rescaled_prob_view(request):
    #Temporary filter for ZTF 2026 events until LSST is online, included

    distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF26').filter(average_master_probability__gt=0.)
    microlensing_objects = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').distinct()[:40]
    #distinct_ids2 = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF25').filter(average_master_probability__gt=0.5)
    #microlensing_objects2 = MicrolensingRadarData.objects.filter(id__in=distinct_ids2).order_by('-average_master_probability').distinct()
    #microlensing_objects = microlensing_objects1.union(microlensing_objects2, all=True)

    try:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})

from django.urls import reverse

class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Very simple first pass: just take the 7 most probable
        # (we know they at least have id and name).
        # This can be modifed with any selector function later.
        # Radar plot top events, for ZTF26 events, waiting for updates       

        distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF26').filter(average_master_probability__gt=0.)
        prio_ids = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').values_list('target_id', flat=True).distinct()[:3]
        target_objects = GalacticTarget.objects.filter(id__in=prio_ids)
        featured = (target_objects)
        context["featured_targets"] = featured
        return context

