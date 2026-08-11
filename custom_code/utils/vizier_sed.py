import math
from datetime import timezone as datetime_timezone

import pandas as pd
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from custom_code.utils.catalog_requests import get_vizier_sed_url, query_vizier_sed


VIZIER_SED_DATA_TYPE = "sed"
VIZIER_SED_SOURCE_NAME = "CDS VizieR SED"
VIZIER_SED_SOURCE_LOCATION = "VizieR SED API"
VIZIER_SED_DEFAULT_RADIUS_ARCSEC = 2.0
VIZIER_SED_DEFAULT_TIMEOUT = 15.0

C_M_S = 299792458.0


def _json_float(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value):
        return None
    return value


def _positive_json_float(value):
    value = _json_float(value)
    if value is None or value <= 0.0:
        return None
    return value


def _json_string(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def _normalise_timestamp(value=None):
    if value is None:
        dt = timezone.now()
    elif isinstance(value, str):
        dt = parse_datetime(value) or timezone.now()
    else:
        dt = value

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, datetime_timezone.utc)

    return dt


def get_vizier_sed_payload_timestamp(payload):
    return _normalise_timestamp((payload or {}).get("queried_at"))


def serialize_vizier_sed_table(
    sed_table,
    *,
    target_name="",
    radius_arcsec=VIZIER_SED_DEFAULT_RADIUS_ARCSEC,
    sed_url="",
    queried_at=None,
    error=None,
):
    queried_at = _normalise_timestamp(queried_at)

    payload = {
        "source": VIZIER_SED_SOURCE_NAME,
        "target_name": target_name or "",
        "radius_arcsec": float(radius_arcsec),
        "query_url": sed_url or "",
        "queried_at": queried_at.isoformat(),
        "n_points": 0,
        "points": [],
        "error": error,
    }

    if error:
        return payload

    if sed_table is None:
        payload["error"] = "No VizieR SED table was returned."
        return payload

    try:
        df = sed_table.to_pandas()
    except Exception as exc:
        payload["error"] = f"Could not convert VizieR SED table to pandas: {exc}"
        return payload

    required_columns = {"sed_freq", "sed_flux"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        payload["error"] = (
            "The VizieR SED table is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )
        return payload

    df["sed_freq"] = pd.to_numeric(df["sed_freq"], errors="coerce")
    df["sed_flux"] = pd.to_numeric(df["sed_flux"], errors="coerce")

    points = []
    for _, row in df.iterrows():
        sed_freq_ghz = _positive_json_float(row.get("sed_freq"))
        sed_flux_jy = _positive_json_float(row.get("sed_flux"))

        if sed_freq_ghz is None or sed_flux_jy is None:
            continue

        frequency_hz = sed_freq_ghz * 1e9
        wavelength_um = (C_M_S / frequency_hz) * 1e6
        nu_fnu_w_m2 = frequency_hz * sed_flux_jy * 1e-26

        if not all(math.isfinite(x) and x > 0.0 for x in [frequency_hz, wavelength_um, nu_fnu_w_m2]):
            continue

        point = {
            "sed_freq_ghz": sed_freq_ghz,
            "sed_flux_jy": sed_flux_jy,
            "frequency_hz": frequency_hz,
            "wavelength_um": wavelength_um,
            "nu_fnu_w_m2": nu_fnu_w_m2,
        }

        if "sed_filter" in df.columns:
            point["sed_filter"] = _json_string(row.get("sed_filter"))

        points.append(point)

    points.sort(key=lambda item: item["wavelength_um"])

    payload["points"] = points
    payload["n_points"] = len(points)

    if not points:
        payload["error"] = "The VizieR SED table contains no positive finite SED points."

    return payload


def query_vizier_sed_payload(
    target,
    *,
    radius_arcsec=VIZIER_SED_DEFAULT_RADIUS_ARCSEC,
    timeout=None,
):
    timeout = timeout if timeout is not None else getattr(
        settings, "VIZIER_SED_TIMEOUT", VIZIER_SED_DEFAULT_TIMEOUT
    )
    queried_at = timezone.now()
    target_name = getattr(target, "name", "")

    ra = _json_float(getattr(target, "ra", None))
    dec = _json_float(getattr(target, "dec", None))
    sed_url = get_vizier_sed_url(ra, dec, radius_arcsec) if ra is not None and dec is not None else ""

    if getattr(target, "type", None) != "SIDEREAL":
        return serialize_vizier_sed_table(
            None,
            target_name=target_name,
            radius_arcsec=radius_arcsec,
            sed_url=sed_url,
            queried_at=queried_at,
            error="VizieR SED plotting is only supported for sidereal targets.",
        )

    if ra is None or dec is None:
        return serialize_vizier_sed_table(
            None,
            target_name=target_name,
            radius_arcsec=radius_arcsec,
            sed_url=sed_url,
            queried_at=queried_at,
            error="VizieR SED plotting requires finite target coordinates.",
        )

    sed_table, sed_error = query_vizier_sed(
        ra,
        dec,
        radius_arcsec=radius_arcsec,
        timeout=timeout,
    )

    return serialize_vizier_sed_table(
        sed_table,
        target_name=target_name,
        radius_arcsec=radius_arcsec,
        sed_url=sed_url,
        queried_at=queried_at,
        error=sed_error,
    )


def get_latest_stored_vizier_sed(target):
    from tom_dataproducts.models import ReducedDatum

    return (
        ReducedDatum.objects.filter(
            target=target,
            data_type=VIZIER_SED_DATA_TYPE,
            source_name=VIZIER_SED_SOURCE_NAME,
        )
        .order_by("-timestamp", "-id")
        .first()
    )


def store_vizier_sed_payload(target, payload):
    from django.db import transaction
    from tom_dataproducts.models import ReducedDatum

    timestamp = get_vizier_sed_payload_timestamp(payload)

    with transaction.atomic():
        existing_qs = ReducedDatum.objects.filter(
            target=target,
            data_type=VIZIER_SED_DATA_TYPE,
            source_name=VIZIER_SED_SOURCE_NAME,
        ).order_by("-timestamp", "-id")

        reduced_datum = existing_qs.first()

        if reduced_datum is None:
            reduced_datum = ReducedDatum.objects.create(
                target=target,
                data_type=VIZIER_SED_DATA_TYPE,
                source_name=VIZIER_SED_SOURCE_NAME,
                source_location=VIZIER_SED_SOURCE_LOCATION,
                timestamp=timestamp,
                value=payload,
            )
            return reduced_datum, True

        existing_qs.exclude(id=reduced_datum.id).delete()

        reduced_datum.timestamp = timestamp
        reduced_datum.value = payload
        reduced_datum.source_location = VIZIER_SED_SOURCE_LOCATION
        reduced_datum.save(update_fields=["timestamp", "value", "source_location"])

        return reduced_datum, False


def fetch_and_store_vizier_sed(
    target,
    *,
    radius_arcsec=VIZIER_SED_DEFAULT_RADIUS_ARCSEC,
    timeout=VIZIER_SED_DEFAULT_TIMEOUT,
):
    payload = query_vizier_sed_payload(
        target,
        radius_arcsec=radius_arcsec,
        timeout=timeout,
    )
    reduced_datum, created = store_vizier_sed_payload(target, payload)
    return reduced_datum, created, payload
