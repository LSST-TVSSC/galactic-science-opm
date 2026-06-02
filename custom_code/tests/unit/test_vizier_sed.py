from io import BytesIO
from unittest.mock import Mock, patch

from astropy.table import Table
import pytest
import requests

from custom_code.utils.catalog_requests import get_vizier_sed_url, query_vizier_sed
from custom_code.utils.vizier_sed import serialize_vizier_sed_table


def _sed_votable_bytes():
    table = Table(
        {
            "sed_freq": [1.0, 10.0],
            "sed_flux": [2.0, 3.0],
            "sed_filter": ["test-a", "test-b"],
        }
    )
    buffer = BytesIO()
    table.write(buffer, format="votable")
    return buffer.getvalue()


def test_get_vizier_sed_url_contains_position_and_radius():
    url = get_vizier_sed_url(123.456789, -12.345678, radius_arcsec=2.0)

    assert "vizier/sed/" in url
    assert "-c=123.45678900%2C-12.34567800" in url
    assert "-c.rs=2.000" in url


@patch("custom_code.utils.catalog_requests.requests.get")
def test_query_vizier_sed_success(mock_get):
    response = Mock()
    response.content = _sed_votable_bytes()
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    table, error = query_vizier_sed(123.4, -12.3)

    assert error is None
    assert table is not None
    assert len(table) == 2
    assert "sed_freq" in table.colnames
    assert "sed_flux" in table.colnames

    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == 5.0
    assert kwargs["params"]["-c"] == "123.40000000,-12.30000000"
    assert kwargs["params"]["-c.rs"] == "2.000"


@patch("custom_code.utils.catalog_requests.requests.get")
def test_query_vizier_sed_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout

    table, error = query_vizier_sed(123.4, -12.3)

    assert table is None
    assert "timed out" in error


@patch("custom_code.utils.catalog_requests.requests.get")
def test_query_vizier_sed_missing_required_columns(mock_get):
    table_without_sed_columns = Table({"foo": [1.0]})
    buffer = BytesIO()
    table_without_sed_columns.write(buffer, format="votable")

    response = Mock()
    response.content = buffer.getvalue()
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    table, error = query_vizier_sed(123.4, -12.3)

    assert table is None
    assert "missing required column" in error


def test_serialize_vizier_sed_table_converts_to_plot_units():
    table = Table(
        {
            "sed_freq": [1.0, 10.0],
            "sed_flux": [2.0, 3.0],
            "sed_filter": ["test-a", "test-b"],
        }
    )

    payload = serialize_vizier_sed_table(
        table,
        target_name="TEST_TARGET",
        radius_arcsec=2.0,
        sed_url="https://example.invalid/sed",
    )

    assert payload["error"] is None
    assert payload["target_name"] == "TEST_TARGET"
    assert payload["radius_arcsec"] == 2.0
    assert payload["query_url"] == "https://example.invalid/sed"
    assert payload["n_points"] == 2

    first_point = payload["points"][0]
    second_point = payload["points"][1]

    assert first_point["sed_freq_ghz"] == 10.0
    assert first_point["sed_flux_jy"] == 3.0
    assert first_point["sed_filter"] == "test-b"
    assert first_point["frequency_hz"] == pytest.approx(1.0e10)
    assert first_point["wavelength_um"] == pytest.approx(29979.2458)
    assert first_point["nu_fnu_w_m2"] == pytest.approx(3.0e-16)

    assert first_point["wavelength_um"] < second_point["wavelength_um"]


def test_serialize_vizier_sed_table_reports_missing_columns():
    table = Table({"foo": [1.0]})

    payload = serialize_vizier_sed_table(table)

    assert payload["n_points"] == 0
    assert payload["points"] == []
    assert "missing required columns" in payload["error"]


def test_serialize_vizier_sed_table_ignores_non_positive_points():
    table = Table(
        {
            "sed_freq": [10.0, 0.0, 5.0],
            "sed_flux": [3.0, 2.0, -1.0],
            "sed_filter": ["good", "zero-frequency", "negative-flux"],
        }
    )

    payload = serialize_vizier_sed_table(table)

    assert payload["error"] is None
    assert payload["n_points"] == 1
    assert payload["points"][0]["sed_filter"] == "good"


@pytest.mark.django_db
def test_recent_and_priority_targets_does_not_filter_after_slice():
    from custom_code.management.commands.populate_vizier_seds import (
        _recent_and_priority_targets,
    )
    from custom_code.target_models import (
        GalacticTarget,
        MicrolensingRadarData,
    )

    target = GalacticTarget.objects.create(
        name="ZTF_TEST_TARGET",
        type="SIDEREAL",
        ra=123.4,
        dec=-12.3,
        known_variability="queried",
        known_extragalactic=(
            GalacticTarget.CatalogFlag.NOT_IN_GLADE_PLUS
        ),
    )

    # Keep the target outside the recent-target window so it must be
    # selected through the priority/radar queryset.
    from datetime import timedelta
    from django.utils import timezone

    GalacticTarget.objects.filter(pk=target.pk).update(
        modified=timezone.now() - timedelta(days=30)
    )

    MicrolensingRadarData.objects.create(
        target=target,
        average_master_probability=0.8,
    )

    selected_targets = _recent_and_priority_targets(
        "ZTF",
        recent_days=3,
        priority_limit=1,
    )

    assert target.id in {
        selected_target.id for selected_target in selected_targets
    }
