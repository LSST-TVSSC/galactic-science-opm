import datetime

import astropy.units as u
import numpy as np
import plotly.graph_objs as go
from astropy.coordinates import get_body, get_sun
from astropy.time import Time
from django import template
from plotly import offline

register = template.Library()


def get_subpoint(object_coord, time):
    lat = object_coord.dec.degree
    lon = (
        (object_coord.ra - time.sidereal_time("mean", "greenwich"))
        .wrap_at(180 * u.deg)
        .degree
    )
    return lat, lon


def get_astronomical_circle_boundary(dec_deg, ra_deg, radius_deg, n_points=350):
    dec_rad, ra_rad, r_rad = np.radians([dec_deg, ra_deg, radius_deg])
    bearings = np.linspace(0, 2 * np.pi, n_points)
    decs_out = np.arcsin(
        np.sin(dec_rad) * np.cos(r_rad)
        + np.cos(dec_rad) * np.sin(r_rad) * np.cos(bearings)
    )
    ras_out = ra_rad + np.arctan2(
        np.sin(bearings) * np.sin(r_rad) * np.cos(dec_rad),
        np.cos(r_rad) - np.sin(dec_rad) * np.sin(decs_out),
    )
    decs_deg_out = np.degrees(decs_out)
    ras_deg_out = np.degrees(ras_out)
    ras_deg_out = ras_deg_out % 360

    return decs_deg_out, ras_deg_out


def get_circle_boundary(clat, clon, radius_deg, n_points=350):
    clat_rad, clon_rad, r_rad = np.radians([clat, clon, radius_deg])
    bearings = np.linspace(0, 2 * np.pi, n_points)

    lats = np.arcsin(
        np.sin(clat_rad) * np.cos(r_rad)
        + np.cos(clat_rad) * np.sin(r_rad) * np.cos(bearings)
    )
    lons = clon_rad + np.arctan2(
        np.sin(bearings) * np.sin(r_rad) * np.cos(clat_rad),
        np.cos(r_rad) - np.sin(clat_rad) * np.sin(lats),
    )
    lons_deg = np.degrees(lons)
    lons_wrapped = np.unwrap(lons_deg, period=360)

    return np.degrees(lats), lons_wrapped  # (np.degrees(lons) + 180) % 360 - 180


def geo_latlon_mpc(lon_east, cos_val, sin_val):
    lat = np.degrees(np.atan2(sin_val, cos_val))
    lon = lon_east if lon_east <= 180 else lon_east - 360
    return lon, lat


@register.inclusion_tag("earth_visibility_plot/earth_visibility.html")
def earth_visibility_plot(targets=None):
    try:
        values = [
            targets.dec,
            targets.ra,
        ]
    except Exception as e:
        values = [0.0, 0.0]
        print(e)
    sites_mpc = (
        ("262", 289.26626, 0.873440, -0.486052, "La Silla"),
        ("X11", 291.59604, 0.909953, -0.414324, "VLT"),
        ("413", 149.0661, 0.85560, -0.51626, "AAT"),
        ("711", 255.9785, 0.86114, +0.50731, "McDonald"),
        ("L09", 20.80987, 0.845559, -0.532619, "SAAO"),
        ("371", 133.5965, 0.82433, +0.56431, "Tokyo-Okayama"),
        ("T09", 204.52396, 0.941711, +0.337239, "Maunakea"),
        ("V07", 249.1219, 0.85208, +0.52234, "Mount Hopkins"),
        ("950", 342.1176, 0.87764, +0.47847, "La Palma"),
    )

    current_utc = datetime.datetime.now(datetime.timezone.utc)
    current_time = Time(current_utc, scale="utc")
    sun_coord = get_sun(current_time)
    moon_coord = get_body("moon", current_time)

    sun_lat, sun_lon = get_subpoint(sun_coord, current_time)
    moon_lat, moon_lon = get_subpoint(moon_coord, current_time)

    target_lats_30, target_lons_30 = get_astronomical_circle_boundary(
        values[0], values[1], 30.0, n_points=350
    )
    term_lats, term_lons = get_circle_boundary(
        sun_lat, sun_lon, radius_deg=90, n_points=350
    )

    fig = go.Figure()

    fig.update_layout(font={"color": "#F4F1EA"})

    observatories = []
    for code, lon_e, c, s, name in sites_mpc:
        if lon_e is None:
            observatories.append({"code": code, "name": name, "lon": None, "lat": None})
            continue
        lon, lat = geo_latlon_mpc(lon_e, c, s)
        observatories.append({"code": code, "name": name, "lon": lon, "lat": lat})

    for obs in observatories:
        if obs["lon"] is None:
            continue
        fig.add_trace(
            go.Scattergeo(
                lon=[obs["lon"]],
                lat=[obs["lat"]],
                mode="markers",
                marker={"size": 10, "color": "darkblue", "symbol": "circle"},
                name=f"{obs['name']}",
                showlegend=False,
            )
        )
    # highlight our special observatory
    rubin_lat = -30.2446
    rubin_lon = -70.7494
    fig.add_trace(
        go.Scattergeo(
            lon=[rubin_lon],
            lat=[rubin_lat],
            mode="markers",
            marker={"size": 12, "color": "white", "symbol": "star"},
            name="Rubin Observatory",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lon=term_lons,
            lat=term_lats,
            mode="lines",
            marker={"size": 4, "color": "rgb(68, 85, 90)"},
            name="Day/Night",
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lon=target_lons_30,
            lat=target_lats_30,
            mode="lines",
            marker={"size": 4, "color": "rgb(255, 140, 0)"},
            name="Target > 30°",
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lon=[sun_lon],
            lat=[sun_lat],
            mode="markers",
            marker={"size": 14, "color": "yellow", "symbol": "circle"},
            name="Sun (zenith)",
        )
    )

    fig.add_trace(
        go.Scattergeo(
            lon=[moon_lon],
            lat=[moon_lat],
            mode="markers",
            marker={"size": 10, "color": "darkgray", "symbol": "circle"},
            name="Moon (zenith)",
        )
    )
    fig.update_layout(
        title="Target Visibility",
        paper_bgcolor="rgb(0, 0, 0)",
        plot_bgcolor="rgb(0, 0, 0)",
        font={"size": 17},
        geo={
            "bgcolor": "rgb(0, 0, 0)",
            "showland": True,
            "landcolor": "rgb(35, 40, 25)",
            "showcountries": True,
            "countrycolor": "rgb(20, 10, 10)",
            "showocean": True,
            "oceancolor": "rgb(25, 35, 40)",
            "showlakes": True,
            "lakecolor": "rgb(40, 40, 40)",
            "projection_type": "natural earth",
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.05,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 19},
        },
    )

    figure = offline.plot(
        fig, output_type="div", show_link=False, include_plotlyjs=False
    )

    return {"figure": figure}
