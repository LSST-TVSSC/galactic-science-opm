import math

from django import template
from custom_code.target_models import MicrolensingModel
from custom_code.utils.catalog_requests import get_vizier_sed_url
from custom_code.utils.vizier_sed import (
    VIZIER_SED_DEFAULT_RADIUS_ARCSEC,
    get_latest_stored_vizier_sed,
)
from sed_plots.permissions import can_fetch_sed
from sed_plots.plotting import make_sed_plot


register = template.Library()


def _valid_magnitude(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(value) and value > 0.0


def _blend_warning(target):
    model = MicrolensingModel.objects.filter(target=target).order_by("-id").first()

    if model is None:
        return None, ""

    source_mag = getattr(model, "source_mag", None)
    blend_mag = getattr(model, "blend_mag", None)

    if not (_valid_magnitude(source_mag) and _valid_magnitude(blend_mag)):
        return None, ""

    blend_to_source_flux = 10 ** (-0.4 * (float(blend_mag) - float(source_mag)))

    if blend_to_source_flux >= 1.0:
        return (
            "danger",
            "Strong blending warning: the fitted blend flux is comparable to or "
            f"larger than the fitted source flux (F_blend/F_source ≈ {blend_to_source_flux:.2f}). "
            "The archive SED should not be interpreted as the source SED.",
        )

    if blend_to_source_flux >= 0.25:
        return (
            "warning",
            "Blending warning: the fitted blend flux is a non-negligible fraction "
            f"of the fitted source flux (F_blend/F_source ≈ {blend_to_source_flux:.2f}). "
            "The archive SED may be significantly contaminated.",
        )

    return None, ""


@register.inclusion_tag("sed_plots/vizier_sed.html", takes_context=True)
def vizier_sed(context, target, radius_arcsec=VIZIER_SED_DEFAULT_RADIUS_ARCSEC):
    warning_level, warning_text = _blend_warning(target)
    sed_url = get_vizier_sed_url(target.ra, target.dec, radius_arcsec)
    request = context.get("request")
    user = getattr(request, "user", None)
    user_can_fetch_sed = can_fetch_sed(user)

    context = {
        "target": target,
        "sed_url": sed_url,
        "figure": None,
        "sed_error": None,
        "warning_level": warning_level,
        "warning_text": warning_text,
        "queried_at": None,
        "can_fetch_sed": user_can_fetch_sed,
    }

    reduced_datum = get_latest_stored_vizier_sed(target)

    if reduced_datum is None:
        context["sed_error"] = (
            "No stored VizieR SED data are available for this target. "
            "Run populate_vizier_seds to fetch and store the SED."
        )
        return context

    payload = reduced_datum.value or {}
    context["sed_url"] = payload.get("query_url") or sed_url
    context["queried_at"] = reduced_datum.timestamp

    payload_error = payload.get("error")
    if payload_error:
        context["sed_error"] = payload_error
        return context

    figure, plot_error = make_sed_plot(payload.get("points", []), target.name)
    if plot_error:
        context["sed_error"] = plot_error
        return context

    context["figure"] = figure
    return context
