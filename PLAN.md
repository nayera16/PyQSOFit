# Plan: export broad C IV profile measurements for asymmetry work

## Objective

Extend `example/example_civ_batch.ipynb` so that each target/model row contains the broad C IV profile measurements needed to calculate three asymmetry statistics in a separate repository, together with uncertainties derived using the notebook's existing MCMC error convention.

The notebook will not calculate the new asymmetry statistics themselves. The existing `CIV_asym` calculation and all existing fit outputs will remain in place.

## Scope and constraints

- Do not change the PyQSOFit configuration, continuum fit, absorption rejection, line fit, MCMC configuration, model grid, or target loop.
- Do not change or remove the existing blueshift or asymmetry calculations.
- Reconstruct only the composite broad C IV component, `CIV_br`.
- Never add `CIV_na` to the profile used for the new measurements.
- Use the fitted smooth Gaussian profile rather than observed pixels.
- Use the existing MCMC samples in `q.gauss_result_all` and the existing uncertainty definition:
  
  `error = (84th percentile - 16th percentile) / 2`.
- Do not add new fitting diagnostics, quality flags, plots, or validation cells.
- Do not execute the notebook as part of this change.

## Measurements to export

All wavelengths are rest-frame Angstroms.

### Cumulative-flux measurements

These are sufficient for the Zakamska & Greene relative asymmetry. The external calculation can use wavelengths directly because any common linear wavelength-to-velocity transformation cancels from the dimensionless ratio.

| Measurement | Output column | Error column |
| --- | --- | --- |
| 5% cumulative broad C IV flux | `CIV_lam_p05_A` | `CIV_lam_p05_err_mcmc_A` |
| 50% cumulative broad C IV flux | `CIV_lam_p50_A` | `CIV_lam_p50_err_mcmc_A` |
| 95% cumulative broad C IV flux | `CIV_lam_p95_A` | `CIV_lam_p95_err_mcmc_A` |

The external repository can calculate:

```text
R = ((lambda_95 - lambda_50) - (lambda_50 - lambda_05))
    / (lambda_95 - lambda_05)
```

### Fractional-height measurements

| Measurement | Output column | Error column |
| --- | --- | --- |
| Blue crossing at 15% of peak | `CIV_lam_blue_15pct_A` | `CIV_lam_blue_15pct_err_mcmc_A` |
| Red crossing at 15% of peak | `CIV_lam_red_15pct_A` | `CIV_lam_red_15pct_err_mcmc_A` |
| Blue crossing at 25% of peak | `CIV_lam_blue_25pct_A` | `CIV_lam_blue_25pct_err_mcmc_A` |
| Red crossing at 25% of peak | `CIV_lam_red_25pct_A` | `CIV_lam_red_25pct_err_mcmc_A` |
| Blue crossing at 80% of peak | `CIV_lam_blue_80pct_A` | `CIV_lam_blue_80pct_err_mcmc_A` |
| Red crossing at 80% of peak | `CIV_lam_red_80pct_A` | `CIV_lam_red_80pct_err_mcmc_A` |
| Wavelength of peak broad-profile flux | `CIV_lam_peak_A` | `CIV_lam_peak_err_mcmc_A` |

The 15% and 80% crossings provide the inputs for the Wolf core-to-base statistic. The 25% crossings and peak wavelength provide the inputs for `AI(1/4)`.

## Profile reconstruction

Add a new helper dedicated to the new measurements. Do not alter `broad_half_wavelengths()`, because it supplies the existing blueshift and asymmetry outputs.

The new helper will:

1. Call `gaussian_params(q, 'CIV_br', sample_index=...)` so that only the named composite broad component is included.
2. Construct a fine log-wavelength grid covering the fitted broad components from the smallest `center - 6 sigma` to the largest `center + 6 sigma`.
3. Use 5,000 grid points. This affects only post-fit measurement and does not alter the fitted model.
4. Evaluate the sum of all `CIV_br` Gaussians on that grid.
5. Identify the wavelength of the global maximum as the peak wavelength.
6. For each of 15%, 25%, and 80% of peak flux, linearly interpolate the nearest blue and red crossings bracketing the global peak.
7. Integrate the profile as `F_lambda d_lambda` with trapezoids and interpolate the wavelengths at 5%, 50%, and 95% of total cumulative model flux.
8. Return the ten measurements in a dictionary. If no valid broad profile is available, return `NaN` for each measurement, matching the notebook's existing failure behavior.

## MCMC uncertainties

Extend `broad_profile_mcmc_results()` without changing its current outputs.

For each existing MCMC line-parameter sample:

1. Call the new broad-profile measurement helper with that `sample_index`.
2. Collect the posterior values of all ten measurements.
3. Pass each collection to the existing `posterior_error()` function.
4. Add the resulting ten measurement errors to the returned dictionary.

No new asymmetry value or asymmetry error will be calculated. These are marginal measurement uncertainties; covariance between measurements is not exported under this minimal scope.

## Batch output changes

In `fit_target_model()`:

1. Call the new measurement helper once for the best-fit Gaussian parameters.
2. Keep the existing calls to `broad_half_wavelengths()`, `blueshift_calc()`, `asym_calc()`, and `broad_profile_mcmc_results()`.
3. Add the ten best-fit wavelength columns and ten MCMC error columns listed above to the output row.
4. Leave all existing columns unchanged.

No changes are required in `data_calculations.py`, because the notebook can obtain every requested measurement uncertainty directly from the existing MCMC samples without calculating the new asymmetry statistics.

## Non-executing verification

After editing:

- Confirm that the notebook remains valid JSON.
- Parse the modified Python cells to confirm syntax validity.
- Inspect the diff to verify that no fit settings or existing asymmetry code changed.
- Do not run any notebook cells or fits.
