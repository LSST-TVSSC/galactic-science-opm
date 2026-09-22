import datetime
import os
import tempfile
import zipfile
from datetime import timedelta

import numpy as np
from astropy.time import Time
from django.conf import settings
from django.contrib.auth.models import User
from django.core import management
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError, connection, connections
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from tom_dataproducts.models import PhotometryReducedDatum
from tom_dataproducts.sharing import get_sharing_destination_options
from tom_targets.forms import TargetShareForm
from tom_targets.models import TargetName
from tom_targets.views import TargetDetailView, TargetShareView

from custom_code.target_models import (
    Classification,
    GalacticTarget,
    MicrolensingParameterModel,
    MicrolensingRadarData,
)
from custom_code.utils.catalog_requests import NOT_IN_ANY_CATALOG


def microlensing_model_view(request):
    microlensing_models = MicrolensingParameterModel.objects.all()[:30]
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


def microlensing_rescaled_prob_view_ztf25(request):

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

    current_year = str(datetime.datetime.now(tz=datetime.timezone.utc).date().year)
    distinct_ids_queried = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains="ZTF")
        .exclude(target__name__icontains=f"ZTF{current_year[2:]}")
        .filter(average_master_probability__gt=0.0)
        .filter(target__known_variability__icontains="queried")
    )
    microlensing_objects_queried = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried)
        .order_by("-average_master_probability")
        .distinct()
    )[:1500]

    context = {
        "microlensing_objects_queried": calculate_metadata(
            microlensing_objects_queried
        ),
    }

    try:
        return render(request, "custom_code/ztf_2025_and_before.html", context)
    except ObjectDoesNotExist:
        return render(request, "custom_code/ztf_2025_and_before.html", context)


def microlensing_rescaled_prob_view(request):

    def get_latest_photometry(target):
        prd = (
            PhotometryReducedDatum.objects.filter(target=target)
            .order_by("-timestamp")
            .first()
        )
        if prd:
            return prd.brightness, prd.bandpass
        return None, None

    def calculate_metadata(queryset):
        """Prepare age for easier ranking"""
        processed_list = []
        for obj in queryset:
            age_days = (timezone.now() - obj.target.created).days
            latest_mag, latest_band = get_latest_photometry(obj.target)
            processed_list.append(
                {
                    "object": obj,
                    "age_days": age_days,
                    "latest_mag": latest_mag,
                    "latest_band": latest_band,
                }
            )
        return processed_list

    current_year = str(datetime.datetime.now(tz=datetime.timezone.utc).date().year)
    distinct_ids = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(target__name__icontains=f"ZTF{current_year[2:]}")
        .filter(average_master_probability__gt=0.0)
        .exclude(target__known_variability__icontains="queried")
    )
    microlensing_objects = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids)
        .order_by("-average_master_probability")
        .distinct()[:70]
    )

    distinct_ids_queried = (
        MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
        .distinct("target_id")
        .filter(
            Q(target__name__icontains=f"ZTF{current_year[2:]}")
            | Q(target__name__icontains=f"OGLE-{current_year}")
        )
        .filter(average_master_probability__gt=0.0)
        .filter(target__known_variability__icontains="queried")
    )

    microlensing_objects_queried = (
        MicrolensingRadarData.objects.filter(id__in=distinct_ids_queried)
        .order_by("-average_master_probability")
        .distinct()[:100]
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

    ogle_targets = GalacticTarget.objects.filter(
        Q(name__icontains=f"OGLE-{current_year}")
        | Q(name__icontains=f"KMT-{current_year}")
    )
    ztf_aliases = TargetName.objects.filter(
        name__icontains="ZTF", target_id__in=ogle_targets.values_list("id", flat=True)
    )

    ztf_alias_map = {a.target_id: a.name for a in ztf_aliases}

    ogle_ztf_targets = ogle_targets.filter(id__in=ztf_alias_map.keys())

    microlensing_objects_ogle_ztf = []
    for t in ogle_ztf_targets:
        obj = (
            MicrolensingRadarData.objects.filter(target=t)
            .order_by("-updated_at")
            .first()
        )
        if obj is None:
            obj = MicrolensingRadarData(
                target=t,
                average_master_probability=0,
                metric_nsquare=0,
                metric_alerce=0,
                metric_probability_ratio=0,
                metric_alerce_atat=0,
                metric_antares=0,
                metric_planet=0,
                metric_bogus=0,
                updated_at=timezone.now(),
            )
        obj.ztf_alias = ztf_alias_map.get(t.id, "")
        obj.ra = t.ra
        obj.dec = t.dec
        microlensing_objects_ogle_ztf.append(obj)

    microlensing_objects_ogle_ztf.sort(
        key=lambda x: x.average_master_probability or 0, reverse=True
    )
    microlensing_objects_ogle_ztf = microlensing_objects_ogle_ztf[:20]
    context = {
        "microlensing_objects": calculate_metadata(microlensing_objects),
        "microlensing_objects_ogle_ztf": calculate_metadata(
            microlensing_objects_ogle_ztf
        ),
        "microlensing_objects_queried": calculate_metadata(
            microlensing_objects_queried
        ),
        "microlensing_objects_queried_lsst": calculate_metadata(
            microlensing_objects_queried_lsst
        ),
    }

    try:
        return render(request, "custom_code/prob_list.html", context)
    except ObjectDoesNotExist:
        return render(request, "custom_code/prob_list.html", context)


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
        return render(request, "custom_code/prob_list_lsst.html", context)
    except ObjectDoesNotExist:
        return render(request, "custom_code/prob_list_lsst.html", context)


class HomeView(TemplateView):
    template_name = "tom_common/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        AMOUNT_OF_FEATURED_TARGETS = 4
        current_year = str(datetime.datetime.now(tz=datetime.timezone.utc).date().year)
        distinct_ids = (
            MicrolensingRadarData.objects.order_by("target_id", "-updated_at")
            .distinct("target_id")
            .filter(
                Q(target__name__icontains=f"ZTF{current_year[2:]}")
                | Q(target__name__icontains="LSST")
            )
            .filter(target__known_variability=NOT_IN_ANY_CATALOG)
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
            Q(name__icontains=f"ZTF{current_year[2:]}") | Q(name__icontains="LSST"),
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


class GsoOpmTargetShareForm(TargetShareForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["share_destination"].choices = get_sharing_destination_options(
            include_download=False
        )


class GsoOpmTargetShareView(TargetShareView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        target = context["target"]
        initial = {
            "submitter": self.request.user,
            "share_title": f"Updated data for {target.name}",
        }

        form = GsoOpmTargetShareForm(initial=initial)
        context["form"] = form

        return context


# mhundertmark: Comprehensive DE, MCMC and model comparison script tbd


def download_pylima_script(_, pk):
    qs = GalacticTarget.objects.filter(id=pk)
    target = qs[0]
    script_content = f"""# Automatically generated pyLIMA script for target {target.name}
# Created: {datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
# Target ID: {target.id}

import os
import tempfile
import zipfile

import matplotlib.pyplot as plt
import numpy as np
from pyLIMA import event, telescopes
from pyLIMA.fits import TRF_fit
from pyLIMA.models import PSPL_model

zip_path = f"lightcurves_export_{target.name}.zip"
with tempfile.TemporaryDirectory(prefix="lc_") as tmpdir:
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(tmpdir)

    all_files = [f for f in os.listdir(tmpdir) if f.endswith((".dat", ".txt"))]
    if not all_files:
        raise FileNotFoundError("No .dat or .txt files found in the zip archive")
    # Create event
    your_event = event.Event(ra={target.ra},dec={target.dec})
    your_event.name = "PSPL OPM Event {target.name}"
    nmax = 0
    for data_file in all_files:
        # Load data as strings
        data = np.genfromtxt(os.path.join(tmpdir, data_file), comments="#", dtype=str)

        # Extract passband
        passband = str(data[0, 3])

        if "_" in passband:
            telescope_name, camera_filter = passband.rsplit("_", 1)
            telescope_name = f"{{telescope_name}}{{camera_filter}}"
        else:
            telescope_name = passband
            camera_filter = "unknown"

        # Convert first three columns to float
        lightcurve_data = np.column_stack(
            [
                data[:, 0].astype(float),
                data[:, 1].astype(float),
                data[:, 2].astype(float),
            ]
        )
        # Create telescope
        telescope = telescopes.Telescope(
            name=telescope_name,
            camera_filter=camera_filter,
            lightcurve=lightcurve_data,
            lightcurve_names=["time", "mag", "err_mag"],
            lightcurve_units=["JD", "mag", "mag"],
        )

        if len(lightcurve_data) > 3:
            your_event.telescopes.append(telescope)
        if len(lightcurve_data) > nmax:
            nmax = len(lightcurve_data)
            survey = telescope_name

    your_event.find_survey(survey)
    results = []
    # Create PSPL model
    pspl = PSPL_model.PSPLmodel(
        your_event, parallax=["None", 2460000.0], blend_flux_parameter="noblend"
    )
    my_fit = TRF_fit.TRFfit(pspl)
    my_fit.fit()
    my_fit.fit_outputs()
    pspl = PSPL_model.PSPLmodel(
        your_event, parallax=["None", 2460000.0], blend_flux_parameter="ftotal"
    )
    my_fit = TRF_fit.TRFfit(pspl)
    guessed_parameters = my_fit.initial_guess()
    my_fit.fit()
    pspl = PSPL_model.PSPLmodel(
        your_event,
        parallax=["Annual", guessed_parameters[0]],
        blend_flux_parameter="ftotal",
    )
    my_fit = TRF_fit.TRFfit(pspl)
    my_fit.fit()
    my_fit.fit_outputs()
    my_fit.fit_outputs(bokeh_plot=True)
    plt.show()
"""
    # Create response with file download headers
    response = HttpResponse(script_content, content_type="text/x-python")
    response["Content-Disposition"] = (
        f'attachment; filename="observe_{target.id}_{target.name}.py"'
    )
    return response


# mkistner: This was taken from here:
# https://github.com/LCOGT/mop/blob/600eed8c6d420c709a13bb2310e6310e9248a2b7/mop/toolbox/fittools.py
def repackage_lightcurves(qs):
    """Function to sort through a QuerySet of the ReducedDatums for a given event and repackage the data as a
    dictionary of individual lightcurves in PyLIMA-compatible format for different facilities.
    Note that not all of the QuerySet of ReducedDatums may be photometry, so some sorting is required.
    """

    datasets = {}

    for rd in qs:
        if rd.source_name != "Interferometry_predictor":
            # Identify different lightcurves from the filter label given
            passband = rd.bandpass
            lc = datasets.get(passband, [])

            # Append the datapoint to the corresponding dataset
            try:
                lc.append([Time(rd.timestamp).jd, rd.brightness, rd.brightness_error])
            except:
                lc.append([Time(rd.timestamp).jd, rd.brightness, 1.0])

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

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = tmp.name

    qs = GalacticTarget.objects.filter(id=pk)
    target = qs[0]

    red_data = PhotometryReducedDatum.objects.filter(target=target).order_by(
        "timestamp"
    )
    (datasets, _) = repackage_lightcurves(red_data)

    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for data_id, lc in datasets.items():
                file_path = target.name + "_" + data_id + ".txt"
                file_contents = ""
                file_contents += "# JD   mag   mag_error  dataset_ID\n"
                for i in range(0, len(lc), 1):
                    file_contents += (
                        str(lc[i, 0])
                        + " "
                        + str(lc[i, 1])
                        + " "
                        + str(lc[i, 2])
                        + " "
                        + data_id
                        + "\n"
                    )
                zf.writestr(file_path, file_contents)

        response = FileResponse(
            open(tmp_path, "rb"),  # noqa: SIM115
            as_attachment=True,
            filename=f"lightcurves_export_{target.name}.zip",
        )
        response["Content-Type"] = "application/zip"
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
    _ = management.call_command("flush", "--noinput")
    _ = management.call_command("migrate", "--noinput")
    _ = management.call_command("seed_e2e_data")
    return JsonResponse({"status": "seeding_done"}, status=201)


def version(_request):
    return JsonResponse(
        {
            "commit": settings.GIT_COMMIT,
        }
    )


def humanize_bytes(num):
    for unit in ["B", "K", "M", "G", "T"]:
        if abs(num) < 1024:
            return f"{num:.1f}{unit}"
        num /= 1024
    return f"{num:.1f}P"


def get_db_size():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_database_size(current_database())")
        size_bytes = cursor.fetchone()[0]
    return {
        "bytes": size_bytes,
        "human": humanize_bytes(size_bytes),
    }


@cache_page(60)
def metrics(_request):

    now = timezone.now()
    metrics = {
        "commit": settings.GIT_COMMIT,
        "new_users_last_24h": User.objects.filter(
            date_joined__gte=now - timedelta(hours=24)
        ).count(),
        "pending_users": User.objects.filter(is_active=False).count(),
        "new_targets_last_24h": GalacticTarget.objects.filter(
            created__gte=now - timedelta(hours=24)
        ).count(),
        "new_targets_last_48h": GalacticTarget.objects.filter(
            created__gte=now - timedelta(hours=48)
        ).count(),
        "new_targets_last_72h": GalacticTarget.objects.filter(
            created__gte=now - timedelta(hours=72)
        ).count(),
        "new_targets_last_96h": GalacticTarget.objects.filter(
            created__gte=now - timedelta(hours=96)
        ).count(),
        "db_size": get_db_size(),
    }
    return JsonResponse(metrics)
