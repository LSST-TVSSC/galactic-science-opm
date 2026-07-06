import io
import os
import tempfile
import zipfile
from astropy.time import Time
import numpy as np
from tom_dataproducts.models import ReducedDatum
from django.conf import settings
from django.core import management
from django.db import OperationalError, connections
from django.http import FileResponse, JsonResponse
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from custom_code.target_models import GalacticTarget, MicrolensingParameterModel
from custom_code.target_models import Classification
from custom_code.target_models import MicrolensingRadarData
from django.db.models import Q
from django.views.generic import TemplateView
from django.utils import timezone

from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG
from tom_targets.views import TargetDetailView
def microlensing_model_view(request):
    microlensing_models = MicrolensingParameterModel.objects.all()[
        :30
    ]
    try:
        return render(
            request,
            "custom_code/model_list.html",
            {"microlensing_models": microlensing_models},
        )
    except ObjectDoesNotExist:
        return render(
            request,
            "custom_code/model_list.html",
            {"microlensing_models": microlensing_models},
        )


def microlensing_prob_view(request):

    distinct_ids = Classification.objects.order_by("target_id", "-updated_at").distinct(
        "target_id"
    )
    microlensing_objects_class1 = (
        Classification.objects.filter(id__in=distinct_ids)
        .order_by("-prob_class1")
        .filter(prob_class1__gt=0.0)
    )

    try:
        return render(
            request,
            "custom_code/prob_list.html",
            {"microlensing_objects_class1": microlensing_objects_class1},
        )
    except ObjectDoesNotExist:
        return render(
            request,
            "custom_code/prob_list.html",
            {"microlensing_objects_class1": microlensing_objects_class1},
        )

def microlensing_rescaled_prob_view(request):

    def calculate_metadata(queryset):
        """Prepare age for easier ranking"""
        processed_list = []
        for obj in queryset:
            age_days = (timezone.now() - obj.target.created).days
            processed_list.append(
                {
                    "object": obj,
                    "age_days": age_days,
                }
            )
        return processed_list

    distinct_ids = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains="ZTF")
        .filter(average_master_probability__gt=0.0)
        .exclude(target__known_variability__icontains="queried")
    )
    microlensing_objects = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids)
        .order_by("-average_master_probability")
        .distinct()[:125]
    )

    distinct_ids_queried = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains="ZTF")
        .filter(average_master_probability__gt=0.0)
        .filter(target__known_variability__icontains="queried")
    )
    microlensing_objects_queried = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried)
        .order_by("-average_master_probability")
        .distinct()[:125]
    )

    distinct_ids_queried_lsst = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains="LSST")
        .filter(average_master_probability__gt=0.0)
        .filter(target__known_variability__icontains="queried")
    )
    microlensing_objects_queried_lsst = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried_lsst)
        .order_by("-average_master_probability")
        .distinct()[:10]
    )

    context = {
        "microlensing_objects": calculate_metadata(microlensing_objects),
        "microlensing_objects_queried": calculate_metadata(
            microlensing_objects_queried
        ),
        "microlensing_objects_queried_lsst": calculate_metadata(
            microlensing_objects_queried_lsst
        ),
    }

    try:
        return render(request, 'custom_code/prob_list.html', context)
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list.html', context)


def microlensing_rescaled_prob_view_lsst(request):

    def calculate_metadata(queryset):
        """Prepare age for easier ranking"""
        processed_list = []
        for obj in queryset:
            age_days = (timezone.now() - obj.target.created).days
            processed_list.append(
                {
                    "object": obj,
                    "age_days": age_days,
                }
            )
        return processed_list


    distinct_ids_queried_lsst = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains="LSST")
        .filter(average_master_probability__gt=0.0)
    )
    microlensing_objects_queried_lsst = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried_lsst)
        .order_by("-average_master_probability")
        .distinct()[:150]
    )

    context = {
        "microlensing_objects_queried_lsst": calculate_metadata(
            microlensing_objects_queried_lsst
        ),
    }

    try:
        return render(request, 'custom_code/prob_list_lsst.html', context)
    except ObjectDoesNotExist:
        return render(request, 'custom_code/prob_list_lsst.html', context)

class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        AMOUNT_OF_FEATURED_TARGETS = 4
        distinct_ids = (
            MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
            .distinct("target_id")
            .filter(Q(target__name__icontains="ZTF26") | Q(target__name__icontains="LSST"))
            .filter(target__known_variability = NOT_IN_ANY_CATALOG)
            .filter(average_master_probability__gt=0.0)
        )
        prio_ids = (
            MicrolensingRadarData.objects.filter(id__in=distinct_ids)
            .order_by("-average_master_probability")
            .values_list("target_id", flat=True)
            .distinct()[:AMOUNT_OF_FEATURED_TARGETS]
        )

        target_map = GalacticTarget.objects.in_bulk(prio_ids)
        featured = [target_map[i] for i in prio_ids if i in target_map]
        total = GalacticTarget.objects.filter(
            Q(name__icontains="ZTF26") | Q(name__icontains="LSST"),
        ).count()
        context["featured_targets"] = featured[:AMOUNT_OF_FEATURED_TARGETS]
        context["total_amount_of_targets"] = total
        return context


class GsoOpmTargetDetailView(TargetDetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = self.object
        context["latest_parameter_models"] = target.latest_parameter_models()
        return context

# mkistner: This was taken from here: 
# https://github.com/LCOGT/mop/blob/600eed8c6d420c709a13bb2310e6310e9248a2b7/mop/toolbox/fittools.py
def repackage_lightcurves(qs):
    """Function to sort through a QuerySet of the ReducedDatums for a given event and repackage the data as a
     dictionary of individual lightcurves in PyLIMA-compatible format for different facilities.
     Note that not all of the QuerySet of ReducedDatums may be photometry, so some sorting is required.
     """

    datasets = {}

    for rd in qs:
        if rd.data_type == 'photometry' and rd.source_name != 'Interferometry_predictor':
            # Identify different lightcurves from the filter label given
            passband = rd.value['filter']
            if passband in datasets.keys():
                lc = datasets[passband]
            else:
                lc = []

            # Append the datapoint to the corresponding dataset
            try:
                lc.append([Time(rd.timestamp).jd, rd.value['magnitude'], rd.value['error']])
            except:
                lc.append([Time(rd.timestamp).jd, rd.value['magnitude'], 1.0])

            datasets[passband] = lc

    # Count the total number of datapoints available, and convert the
    # accumulated lightcurves into numpy arrays:
    ndata = 0
    for passband, lc in datasets.items():
        ndata += len(lc)
        datasets[passband] = np.array(lc)

    return datasets, ndata

# mkistner: the export part was adapted from here:
# https://github.com/LCOGT/mop/blob/600eed8c6d420c709a13bb2310e6310e9248a2b7/mop/management/commands/download_event_lc_data.py
def download_lightcurve_data_for_target(_, pk):

    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name

    qs = GalacticTarget.objects.filter(id=pk)
    target = qs[0]

    red_data = ReducedDatum.objects.filter(target=target).order_by("timestamp")
    (datasets, _) = repackage_lightcurves(red_data)

    try:
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for data_id, lc in datasets.items():
                file_path = target.name +'_'+data_id+'.txt'
                file_contents = ""
                file_contents += ('# JD   mag   mag_error  dataset_ID\n')
                for i in range(0,len(lc),1):
                    file_contents += (str(lc[i,0])+' '+str(lc[i,1])+' '+str(lc[i,2])+' '+data_id+'\n')
                zf.writestr(file_path, file_contents)
                
        response = FileResponse(open(tmp_path, 'rb'), as_attachment=True, filename=f"lightcurves_export_{target.name}.zip")
        response['Content-Type'] = 'application/zip'
        return response
    finally:
        os.unlink(tmp_path)

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
    _ = management.call_command(
        "migrate",
        '--noinput'
    )
    _ = management.call_command(
        "seed_e2e_data"
    )
    return JsonResponse({"status": "seeding_done"}, status=201)

def version(_request):
    return JsonResponse({
        "commit": settings.GIT_COMMIT,
    })
