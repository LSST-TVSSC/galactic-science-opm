from django.core import management
from django.db import OperationalError, connections
from django.http import JsonResponse
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
from django.utils import timezone
from datetime import datetime
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

    def calculate_metadata(queryset):
        """Prepare age for easier ranking"""
        processed_list = []
        for obj in queryset:
            age_days = (timezone.now() - obj.target.created).days
            processed_list.append({
                'object': obj,
                'age_days': age_days,
            })
        return processed_list

    distinct_ids = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF').filter(average_master_probability__gt=0.).exclude(target__known_variability__icontains="queried")
    microlensing_objects = MicrolensingRadarData.objects.filter(id__in=distinct_ids).order_by('-average_master_probability').distinct()[:35]
    
    distinct_ids_queried = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='ZTF').filter(average_master_probability__gt=0.).filter(target__known_variability__icontains="queried")
    microlensing_objects_queried = MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried).order_by('-average_master_probability').distinct()[:35]

    distinct_ids_queried_lsst = MicrolensingRadarData.objects.order_by('target_id', '-updated_at').distinct('target_id').filter(target__name__icontains='LSST').filter(average_master_probability__gt=0.).filter(target__known_variability__icontains="queried")
    microlensing_objects_queried_lsst = MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried_lsst).order_by('-average_master_probability').distinct()[:35]

    context = {
        'microlensing_objects': calculate_metadata(microlensing_objects),
        'microlensing_objects_queried': calculate_metadata(microlensing_objects_queried),
        'microlensing_objects_queried_lsst': calculate_metadata(microlensing_objects_queried_lsst),
    }

    try:
        return render(request, 'custom_code/prob_list.html', context)
        #return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list.html', context)
        #return render(request, 'custom_code/prob_list.html', {'microlensing_objects': microlensing_objects})
    

class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Very simple first pass: just take the 7 most probable
        # (we know they at least have id and name).
        # This can be modifed with any selector function later.
        # Radar plot top events, for ZTF26 events, waiting for updates       

        distinct_ids = (
            MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
            .distinct("target_id")
            .filter(target__name__icontains="ZTF26")
            .filter(average_master_probability__gt=0.0)
        )
        prio_ids = (
            MicrolensingRadarData.objects.filter(id__in=distinct_ids)
            .order_by("-average_master_probability")
            .values_list("target_id", flat=True)
            .distinct()[:3]
        )
        target_objects = GalacticTarget.objects.filter(id__in=prio_ids)
        featured = target_objects
        context["featured_targets"] = featured
        return context

def health(_request):
    """
    Very simple health endpoint to check when migrations and so on are done.
    """
    database_connection = connections["default"]
    try:
        database_connection.cursor()
    except OperationalError:
        return JsonResponse({"status": "unhealthy"}, status=503)
    
    return JsonResponse({"status": "healthy"}, status=200)

def flush_and_seed(_request):
    """
    FOR TESTING ONLY!
    This endpoint flushes the database and imports test data. 
    It is only added to urlpatterns if SETTINGS.TESTING is True.
    """
    _ = management.call_command(
        "flush",
        '--noinput'
    )
    # mkistner: I am not quite sure if this is really needed
    _ = management.call_command(
        "migrate",
        '--noinput'
    )
    _ = management.call_command(
        "seed_e2e_data"
    )
    return JsonResponse({"status": "seeding_done"}, status=201)


