"""
In this table, we specify the priors / initial conditions and boundaries for the line fitting parameters.
"""

line_priors = np.rec.array([
    
    (1549.06, 'CIV', 1450, 1700, 'CIV_br', br_component, 0.0, 0.0, 1e10, 0.018, 0.002, 0.02157, 0.015, 0, 0, 0, 0.05, 1),
    (1549.06, 'CIV', 1450, 1700, 'CIV_na', na_component, 0.0, 0.0, 1e10, 1e-3, 5e-4, 0.00169, 0.01, 1, 1, 0, 0.002, 1),
    ],
        
    formats='float32,    a20,  float32, float32,      a20,  int32, float32, float32, float32, float32, float32, float32, float32,   int32,  int32,  int32, float32, int32',
    names=' lambda, compname,   minwav,  maxwav, linename, ngauss,  inisca,  minsca,  maxsca,  inisig,  minsig,  maxsig,    voff,  vindex, windex, findex,  fvalue,  vary')
# Header  
hdr1 = fits.Header()
hdr1['lambda'] = 'Vacuum Wavelength in Ang'
hdr1['minwav'] = 'Lower complex fitting wavelength range'
hdr1['maxwav'] = 'Upper complex fitting wavelength range'
hdr1['ngauss'] = 'Number of Gaussians for the line'

# Can be set to negative for absorption lines if you want
hdr1['inisca'] = 'Initial guess of line scale [flux]'
hdr1['minsca'] = 'Lower range of line scale [flux]'
hdr1['maxsca'] = 'Upper range of line scale [flux]'

hdr1['inisig'] = 'Initial guess of linesigma [lnlambda]'
hdr1['minsig'] = 'Lower range of line sigma [lnlambda]'
hdr1['maxsig'] = 'Upper range of line sigma [lnlambda]'

hdr1['voff  '] = 'Limits on velocity offset from the central wavelength [lnlambda]'
hdr1['vindex'] = 'Entries w/ same NONZERO vindex constrained to have same velocity'
hdr1['windex'] = 'Entries w/ same NONZERO windex constrained to have same width'
hdr1['findex'] = 'Entries w/ same NONZERO findex have constrained flux ratios'
hdr1['fvalue'] = 'Relative scale factor for entries w/ same findex'

hdr1['vary'] = 'Whether or not to vary the parameter (set to 0 to fix the line parameter to initial values)'

# Save line info
hdu1 = fits.BinTableHDU(data=line_priors, header=hdr1, name='line_priors')



# --------- In a later cell
lam = 10 ** data[1].data['loglam'] #/ (1+z) # OBS wavelength [A] 
flux = data[1].data['flux']  # OBS flux [erg/s/cm^2/A]
err = 1 / np.sqrt(data[1].data['ivar'])  # 1 sigma error

# S/N mask: down-weight pixels with S/N < 5 
# Robust S/N using absolute flux; avoid divide-by-zero and non-finite values
good = np.isfinite(flux) & np.isfinite(err) & (err > 0)
snr = np.zeros_like(flux, dtype=float)
snr[good] = np.abs(flux[good]) / err[good]

low_snr = snr < 5
# Heavily down-weight low-S/N pixels by inflating their errors
# (avoids NaNs/Inf, keeps array lengths unchanged for QSOFit)
err[low_snr] *= 1e6

# Optional: keep the mask if you want to inspect later
snr_threshold = 5.0
snr_mask_kept = ~low_snr


# ------------ In the first fitting cell 

# Prepare data
q_mle = QSOFit(lam, flux, err, z, ra=ra, dec=dec, plateid=plateid, mjd=mjd, fiberid=fiberid, path=path_ex)

# Double check the installation path with the PCA / Fe template files
print('install path:', q_mle.install_path)

# Change it if you installed them somewhere else
# q_mle.install_path = '/Users/nayera/PyQSOFit/src/pyqsofit'

# Enforce max FWHM = 15,000 km/s for CIV broad components (lnλ units)
with fits.open(os.path.join(path_ex, 'qsopar.fits'), mode='update') as hdul:
    hdu1 = hdul[1]
    mask = hdu1.data['linename'] == 'CIV_br'
    
    # Set maxsig to ln(σ) where FWHM = 15,000 km/s → σ_lnλ ≈ 0.02157
    maxsig_limit = 0.02157

    hdu1.data['maxsig'][mask] = maxsig_limit

    # Optional: ensure 'vary' is 1 so the fitter uses the limits
    hdu1.data['vary'][mask] = 1

    hdul.flush()
    
start = timeit.default_timer()
# Do the fitting

q_mle.Fit(name=quasar_name,  # customize the name of given targets. Default: plate-mjd-fiber
          # prepocessing parameters
          nsmooth=1,  # do n-pixel smoothing to the raw input flux and err spectra
          and_mask=False,  # delete the and masked pixels
          or_mask=False,  # delete the or masked pixels
          reject_badpix=True,  # reject 10 most possible outliers by the test of pointDistGESD
          deredden=False,  # correct the Galactic extinction
          # wave_range=[1445*(1+z),1705*(1+z)],  
          wave_range=[1445,1620], # trim input wavelength **
          wave_mask= mask_arr,  # 2-D array, mask the given range(s) np.array([[2000,3000],[3100,4000]])

          # host decomposition parameters
          decompose_host=False,  # If True, the host galaxy-QSO decomposition will be applied
          host_prior=False, # If True, the code will adopt prior-informed method to assist decomposition. Currently, only 'CZBIN1' and 'DZBIN1' model for QSO PCA are available. And the model for galaxy must be PCA too.
          host_prior_scale=0.2, # scale of prior panelty. Usually, 0.2 works fine for SDSS spectra. Adjust it smaller if you find the prior affect the fitting results too much.

          host_line_mask=True, # If True, the line region of galaxy will be masked when subtracted from original spectra.
          decomp_na_mask=True, # If True, the narrow line region will be masked when perform decomposition
          qso_type='CZBIN1', # PCA template name for quasar
          npca_qso=10, # numebr of quasar templates
          host_type='PCA', # template name for galaxy
          npca_gal=5, # number of galaxy templates
          
          # continuum model fit parameters
          Fe_uv_op=False,  # If True, fit continuum with UV and optical FeII template
          poly=False,  # If True, fit continuum with the polynomial component to account for the dust reddening
          BC=False,  # If True, fit continuum with Balmer continua from 1000 to 3646A
          initial_guess=None,  # Initial parameters for continuum model, read the annotation of this function for detail
          rej_abs_conti=True,  # If True, it will iterately reject 3 sigma outlier absorption pixels in the continuum
          n_pix_min_conti=100,  # Minimum number of negative pixels for host continuuum fit to be rejected.

          # emission line fit parameters
          linefit=True,  # If True, the emission line will be fitted
          rej_abs_line=True,
          # If True, it will iterately reject 3 sigma outlier absorption pixels in the emission lines

          # fitting method selection
          MC=False,
          # If True, do Monte Carlo resampling of the spectrum based on the input error array to produce the MC error array
          MCMC=True,
          # If True, do Markov Chain Monte Carlo sampling of the posterior probability densities to produce the error array (can turn on)
          nsamp=200,
          # The number of trials of the MC process (if MC=True) or number samples to run MCMC chain (if MCMC=True)

          # advanced fitting parameters
          param_file_name='qsopar.fits',  # Name of the qso fitting parameter FITS file.
          nburn=20,  # The number of burn-in samples to run MCMC chain
          nthin=10,  # To set the MCMC chain returns every n samples
          epsilon_jitter=0.,
          # Initial jitter for every initial guass to avoid local minimum. (Under test, not recommanded to change)

          # customize the results
          save_result=True,  # If True, all the fitting results will be saved to a fits file
          save_fits_name= output_file,  # The output name of the result fits
          save_fits_path=path_out,  # The output path of the result fits
          plot_fig=True,  # If True, the fitting results will be plotted
          save_fig=True,  # If True, the figure will be saved
          plot_corner=True,  # Whether or not to plot the corner plot results if MCMC=True

          # debugging mode
          verbose=True,  # turn on (True) or off (False) debugging output
          
          # sublevel parameters for figure plot and emcee
          kwargs_plot={
              'save_fig_path': save_fig_path,#'/Users/nayera/PyQSOFit/CIV_galaxy_spectra_targets/output',  # The output path of the figure
              'broad_fwhm'   : 1200,  # km/s, lower limit that code decide if a line component belongs to broad component
          },
          kwargs_conti_emcee={},
          kwargs_line_emcee={})
       
end = timeit.default_timer()

print(f'Fitting finished in {np.round(end - start, 1)}s')

# attempted to get black line in front of grey masking but did not work
# ax = plt.gca()
# ax.plot(q_mle.wave, q_mle.line_flux, 'k', zorder=10)

matplotlib.pyplot.show()


