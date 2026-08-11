import numpy as np
import pandas as pd
from plotly import offline
import plotly.graph_objs as go


MIN_BLACKBODY_POINTS = 5
MIN_DISTINCT_FILTERS = 5
MIN_POINTS_FOR_SIGMA_CLIPPING = 8
MIN_RETAINED_FRACTION = 0.7


def _points_to_dataframe(points):
    df = pd.DataFrame(points or [])

    required_columns = ["frequency_hz", "wavelength_um", "nu_fnu_w_m2"]
    if df.empty or any(column not in df.columns for column in required_columns):
        return pd.DataFrame()

    for column in required_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if "sed_freq_ghz" in df.columns:
        df["sed_freq_ghz"] = pd.to_numeric(df["sed_freq_ghz"], errors="coerce")
    else:
        df["sed_freq_ghz"] = df["frequency_hz"] / 1e9

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=required_columns)
    df = df[
        (df["frequency_hz"] > 0.0)
        & (df["wavelength_um"] > 0.0)
        & (df["nu_fnu_w_m2"] > 0.0)
    ]

    return df.sort_values("wavelength_um")


def _blackbody_grid_fit(df):
    required_columns = ["frequency_hz", "wavelength_um", "nu_fnu_w_m2"]
    fit_df = df[required_columns].copy()
    fit_df = fit_df.replace([np.inf, -np.inf], np.nan)
    fit_df = fit_df.dropna(subset=required_columns)
    fit_df = fit_df[
        (fit_df["frequency_hz"] > 0.0)
        & (fit_df["wavelength_um"] > 0.0)
        & (fit_df["nu_fnu_w_m2"] > 0.0)
    ]

    if len(fit_df) < MIN_BLACKBODY_POINTS:
        return None

    nu_hz = fit_df["frequency_hz"].to_numpy(dtype=float)
    observed_nu_fnu = fit_df["nu_fnu_w_m2"].to_numpy(dtype=float)

    h = 6.62607015e-34
    k_b = 1.380649e-23
    c = 299792458.0

    log_observed = np.log(observed_nu_fnu)
    temperature_grid = np.geomspace(1500.0, 50000.0, 80)
    best_fit = None

    for temperature in temperature_grid:
        x = h * nu_hz / (k_b * temperature)

        if np.any(x <= 0.0) or np.any(x > 700.0):
            continue

        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            b_nu = (2.0 * h * nu_hz**3 / c**2) / np.expm1(x)
            model_shape = nu_hz * b_nu

        if np.any(~np.isfinite(model_shape)) or np.any(model_shape <= 0.0):
            continue

        log_model_shape = np.log(model_shape)
        log_scale = np.mean(log_observed - log_model_shape)
        residuals = log_observed - (log_scale + log_model_shape)
        score = float(np.mean(residuals**2))

        if best_fit is None or score < best_fit["score"]:
            best_fit = {
                "temperature": float(temperature),
                "log_scale": float(log_scale),
                "score": score,
                "residuals": residuals,
                "fit_df": fit_df,
            }

    return best_fit


def _sigma_clipped_blackbody_fit(df):
    """
    Fit once using all points, then refit after clipping only catastrophic
    log-flux residuals.

    The clipping is deliberately conservative. VizieR SEDs combine heterogeneous
    catalogues, and the long-wavelength tail often contains real excesses or
    aperture/filter effects that a single-temperature blackbody should not erase.
    """

    initial_fit = _blackbody_grid_fit(df)

    if initial_fit is None:
        return None

    residuals = np.asarray(initial_fit["residuals"], dtype=float)
    fit_df = initial_fit["fit_df"].copy()
    finite = np.isfinite(residuals)

    if finite.sum() < MIN_POINTS_FOR_SIGMA_CLIPPING:
        return initial_fit

    median_residual = np.median(residuals[finite])
    mad = np.median(np.abs(residuals[finite] - median_residual))

    if not np.isfinite(mad) or mad <= 0.0:
        return initial_fit

    robust_sigma = 1.4826 * mad

    # Conservative floor: do not clip modest deviations from an approximate
    # blackbody guide. Residuals are natural-log residuals.
    normal_threshold = max(4.0 * robust_sigma, np.log(10.0) * 1.0)

    # Long-wavelength points are often where real excesses, catalogue aperture
    # effects, and filter heterogeneity appear. Keep them unless they are very
    # extreme.
    long_wavelength_cut = fit_df["wavelength_um"].quantile(0.75)
    is_long_wavelength = fit_df["wavelength_um"] >= long_wavelength_cut
    long_wavelength_threshold = max(6.0 * robust_sigma, np.log(10.0) * 1.75)

    abs_residual = np.abs(residuals - median_residual)
    keep = (
        (~is_long_wavelength.to_numpy() & (abs_residual <= normal_threshold))
        | (is_long_wavelength.to_numpy() & (abs_residual <= long_wavelength_threshold))
    )

    # Do not over-prune. If the clipping removes too many points, the model is
    # simply a poor guide for this SED, so keep the all-point fit.
    if (
        keep.sum() < MIN_BLACKBODY_POINTS
        or keep.sum() < MIN_RETAINED_FRACTION * len(keep)
    ):
        return initial_fit

    clipped_df = fit_df.iloc[keep].copy()
    clipped_fit = _blackbody_grid_fit(clipped_df)

    if clipped_fit is None:
        return initial_fit

    clipped_fit["n_clipped"] = int(len(keep) - keep.sum())
    clipped_fit["n_used"] = int(keep.sum())
    return clipped_fit


def _fit_blackbody_continuum(df):
    if len(df) < MIN_BLACKBODY_POINTS:
        return None

    if "sed_filter" in df.columns:
        filters = df["sed_filter"].dropna().astype(str)
        filters = filters[filters.str.strip() != ""]
        if filters.nunique() < MIN_DISTINCT_FILTERS:
            return None

    best_fit = _sigma_clipped_blackbody_fit(df)

    if best_fit is None:
        return None

    fit_df = best_fit["fit_df"]

    wavelength_grid_um = np.geomspace(
        fit_df["wavelength_um"].min(),
        fit_df["wavelength_um"].max(),
        300,
    )

    h = 6.62607015e-34
    k_b = 1.380649e-23
    c = 299792458.0

    nu_grid_hz = c / (wavelength_grid_um * 1e-6)
    temperature = best_fit["temperature"]
    x_grid = h * nu_grid_hz / (k_b * temperature)

    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        b_nu_grid = (2.0 * h * nu_grid_hz**3 / c**2) / np.expm1(x_grid)
        model_nu_fnu = np.exp(best_fit["log_scale"]) * nu_grid_hz * b_nu_grid

    valid = np.isfinite(model_nu_fnu) & (model_nu_fnu > 0.0)

    if valid.sum() < 2:
        return None

    return {
        "wavelength_um": wavelength_grid_um[valid],
        "nu_fnu_w_m2": model_nu_fnu[valid],
        "temperature": best_fit["temperature"],
        "n_clipped": best_fit.get("n_clipped", 0),
        "n_used": best_fit.get("n_used", len(fit_df)),
    }


def make_sed_plot(points, target_name):
    df = _points_to_dataframe(points)

    if df.empty:
        return None, "No stored positive finite VizieR SED points are available for this target."

    if "sed_filter" in df.columns:
        marker_text = df["sed_filter"].fillna("").astype(str)
        hovertemplate = (
            "Wavelength: %{x:.4g} μm<br>"
            "νFν: %{y:.3e} W m⁻²<br>"
            "Filter: %{text}"
            "<extra></extra>"
        )
    else:
        marker_text = None
        hovertemplate = (
            "Wavelength: %{x:.4g} μm<br>"
            "νFν: %{y:.3e} W m⁻²"
            "<extra></extra>"
        )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["wavelength_um"],
            y=df["nu_fnu_w_m2"],
            mode="markers",
            text=marker_text,
            marker=dict(
                size=13,
                opacity=0.77,
                color=df["sed_freq_ghz"],
                colorscale="Jet_r",
                showscale=False,
                line=dict(width=2, color="White"),
            ),
            hovertemplate=hovertemplate,
            name="VizieR SED",
        )
    )

    blackbody_fit = _fit_blackbody_continuum(df)

    if blackbody_fit is not None:
        clipped_suffix = ""
        if blackbody_fit.get("n_clipped", 0):
            clipped_suffix = f", {blackbody_fit['n_clipped']} clipped"

        fig.add_trace(
            go.Scatter(
                x=blackbody_fit["wavelength_um"],
                y=blackbody_fit["nu_fnu_w_m2"],
                mode="lines",
                line=dict(color="White", width=3, dash="dash"),
                name=f"Approx. blackbody guide ({blackbody_fit['temperature']:.0f} K{clipped_suffix})",
                hovertemplate=(
                    "Approx. blackbody guide<br>"
                    f"T ≈ {blackbody_fit['temperature']:.0f} K<br>"
                    f"Points used: {blackbody_fit.get('n_used', 0)}<br>"
                    f"Points clipped: {blackbody_fit.get('n_clipped', 0)}<br>"
                    "Wavelength: %{x:.4g} μm<br>"
                    "νFν: %{y:.3e} W m⁻²"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"VizieR SED for {target_name}",
        template="plotly_dark",
        margin=dict(l=50, r=30, t=60, b=50),
        showlegend=True,
    )
    fig.update_xaxes(type="log", title_text="Wavelength (μm)")
    fig.update_yaxes(
        type="log",
        title_text="νFν (W m⁻²)",
        exponentformat="power",
        showexponent="all",
    )

    return offline.plot(fig, output_type="div", show_link=False, include_plotlyjs=False), None
