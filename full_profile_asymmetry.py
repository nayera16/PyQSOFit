"""Measurements shared by the two C IV full-profile fitting notebooks.

The profile contains every fitted broad and narrow C IV Gaussian. Literature
uncertainties follow asym_calc.py's independent-input approximation; the input
wavelength uncertainties and legacy asymmetry uncertainty use MCMC percentiles.
"""

import numpy as np


INPUT_KEYS = (
    "lam_p05", "lam_p50", "lam_p95",
    "lam_blue_15pct", "lam_red_15pct",
    "lam_blue_25pct", "lam_red_25pct",
    "lam_blue_80pct", "lam_red_80pct", "lam_peak",
)


def input_column(key):
    return f"CIV_{key}_full_profile_A"


def input_error_column(key):
    return f"CIV_{key}_full_profile_err_mcmc_A"


INPUT_COLUMNS = tuple(
    column for key in INPUT_KEYS
    for column in (input_column(key), input_error_column(key))
)

LITERATURE_COLUMNS = (
    "CIV_asym_zg_R_full_profile",
    "CIV_asym_zg_R_full_profile_err_approx",
    "CIV_asym_zg_R_full_profile_norm_0_2",
    "CIV_asym_zg_R_full_profile_norm_0_2_err_approx",
    "CIV_asym_wolf_15_80_full_profile",
    "CIV_asym_wolf_15_80_full_profile_err_approx",
    "CIV_asym_wolf_15_80_full_profile_norm_0_2",
    "CIV_asym_wolf_15_80_full_profile_norm_0_2_err_approx",
    "CIV_asym_4de1_AI_1_4_full_profile",
    "CIV_asym_4de1_AI_1_4_full_profile_err_approx",
    "CIV_asym_4de1_AI_1_4_full_profile_norm_0_2",
    "CIV_asym_4de1_AI_1_4_full_profile_norm_0_2_err_approx",
)

FULL_PROFILE_COLUMNS = (
    "asym_full_profile", "asym_full_profile_err_mcmc",
    *LITERATURE_COLUMNS, *INPUT_COLUMNS,
)


def _posterior_error(values):
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return np.nan
    lo, hi = np.percentile(finite, [16, 84])
    return float((hi - lo) / 2)


def measure_shape(q, gaussian_params, sample_index=None, grid_points=5000, nsigma=6.0):
    """Return flux percentiles, fractional-height crossings, and peak wavelength."""
    empty = {key: np.nan for key in INPUT_KEYS}
    broad = gaussian_params(q, "CIV_br", sample_index=sample_index).reshape(-1, 3)
    narrow = gaussian_params(q, "CIV_na", sample_index=sample_index).reshape(-1, 3)
    params = np.concatenate((broad, narrow), axis=0)
    if params.size == 0 or not np.isfinite(params).all() or np.any(params[:, 2] <= 0):
        return empty

    lnlam = np.linspace(
        np.min(params[:, 1] - nsigma * params[:, 2]),
        np.max(params[:, 1] + nsigma * params[:, 2]),
        grid_points,
    )
    lam = np.exp(lnlam)
    model = np.zeros_like(lam)
    for amp, center, sigma in params:
        model += amp * np.exp(-0.5 * ((lnlam - center) / sigma) ** 2)
    if not np.isfinite(model).all() or np.max(model) <= 0:
        return empty

    i_peak = int(np.argmax(model))
    peak_flux = model[i_peak]

    def crossing(j0, j1, level):
        y0, y1 = model[j0], model[j1]
        if y0 == y1:
            return np.nan
        return float(lam[j0] + (level - y0) * (lam[j1] - lam[j0]) / (y1 - y0))

    def crossings(fraction):
        level = fraction * peak_flux
        left = np.flatnonzero(model[:i_peak] < level)
        right = np.flatnonzero(model[i_peak + 1:] < level)
        if left.size == 0 or right.size == 0:
            return np.nan, np.nan
        j_left = int(left[-1])
        j_right = int(i_peak + 1 + right[0])
        return crossing(j_left, j_left + 1, level), crossing(j_right - 1, j_right, level)

    increments = 0.5 * (model[1:] + model[:-1]) * np.diff(lam)
    cumulative = np.concatenate(([0.0], np.cumsum(increments)))
    if cumulative[-1] <= 0:
        return empty
    p05, p50, p95 = np.interp(
        np.array([0.05, 0.50, 0.95]) * cumulative[-1], cumulative, lam
    )
    b15, r15 = crossings(0.15)
    b25, r25 = crossings(0.25)
    b80, r80 = crossings(0.80)
    return dict(zip(INPUT_KEYS, (p05, p50, p95, b15, r15, b25, r25, b80, r80, lam[i_peak])))


def full_profile_results(q, gaussian_params, legacy_asymmetry, literature):
    """Measure all four full-profile statistics without repeating the MCMC fit."""
    shape = measure_shape(q, gaussian_params)
    samples = getattr(q, "gauss_result_all", None)
    if getattr(q, "MCMC", False) and samples is not None and len(samples):
        posterior_shapes = []
        legacy_samples = []
        for i in range(len(samples)):
            posterior_shapes.append(measure_shape(q, gaussian_params, sample_index=i))
            legacy_samples.append(legacy_asymmetry(q, sample_index=i))
        input_errors = {
            key: _posterior_error([item[key] for item in posterior_shapes])
            for key in INPUT_KEYS
        }
        legacy_error = _posterior_error(legacy_samples)
    else:
        input_errors = {key: np.nan for key in INPUT_KEYS}
        legacy_error = np.nan

    output = {
        "asym_full_profile": legacy_asymmetry(q),
        "asym_full_profile_err_mcmc": legacy_error,
    }
    for key in INPUT_KEYS:
        output[input_column(key)] = float(shape[key])
        output[input_error_column(key)] = float(input_errors[key])

    def v(key):
        return shape[key]

    def e(key):
        return input_errors[key]

    zg = literature.zakamska_greene_r(v("lam_p05"), v("lam_p50"), v("lam_p95"))
    zg_err = literature.zakamska_greene_r_error(
        v("lam_p05"), e("lam_p05"), v("lam_p50"), e("lam_p50"), v("lam_p95"), e("lam_p95")
    )
    wolf = literature.wolf_asymmetry(
        v("lam_blue_15pct"), v("lam_red_15pct"), v("lam_blue_80pct"), v("lam_red_80pct")
    )
    wolf_err = literature.wolf_asymmetry_error(
        v("lam_blue_15pct"), e("lam_blue_15pct"),
        v("lam_red_15pct"), e("lam_red_15pct"),
        v("lam_blue_80pct"), e("lam_blue_80pct"),
        v("lam_red_80pct"), e("lam_red_80pct"),
    )
    ai = literature.ai_quarter(v("lam_blue_25pct"), v("lam_red_25pct"), v("lam_peak"))
    ai_err = literature.ai_quarter_error(
        v("lam_blue_25pct"), e("lam_blue_25pct"),
        v("lam_red_25pct"), e("lam_red_25pct"), v("lam_peak"), e("lam_peak"),
    )
    for name, value, error, blue_sign in (
        ("CIV_asym_zg_R", zg, zg_err, -1),
        ("CIV_asym_wolf_15_80", wolf, wolf_err, 1),
        ("CIV_asym_4de1_AI_1_4", ai, ai_err, -1),
    ):
        output[f"{name}_full_profile"] = float(value)
        output[f"{name}_full_profile_err_approx"] = float(error)
        normalized, normalized_error = literature.scale_bounded_asymmetry(
            value, error, blue_sign=blue_sign
        )
        output[f"{name}_full_profile_norm_0_2"] = float(normalized)
        output[f"{name}_full_profile_norm_0_2_err_approx"] = float(normalized_error)
    return output
