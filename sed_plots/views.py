from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from custom_code.target_models import GalacticTarget
from custom_code.utils.vizier_sed import fetch_and_store_vizier_sed
from sed_plots.permissions import can_fetch_sed


@login_required
@user_passes_test(can_fetch_sed)
def fetch_vizier_sed(request, target_id):
    target = get_object_or_404(GalacticTarget, id=target_id)
    fallback_url = reverse("target-detail", args=[target.id])
    return_url = request.META.get("HTTP_REFERER") or fallback_url

    if request.method != "POST":
        return redirect(return_url)

    _, _, payload = fetch_and_store_vizier_sed(target)

    if payload.get("error"):
        messages.warning(
            request,
            f"Stored VizieR SED response for {target.name}, but the query returned an error: {payload['error']}",
        )
    else:
        messages.success(
            request,
            f"Stored VizieR SED for {target.name}: {payload.get('n_points', 0)} points.",
        )

    return redirect(return_url)
