from multiprocessing import Pool
import os, timeit, glob
from astropy.io import fits

def job(file):
    print(file + '\n')

    data = fits.open(file)

    lam = 10 ** data[1].data['loglam']
    flux = data[1].data['flux']
    err = 1 / np.sqrt(data[1].data['ivar'])
    ra = data[0].header['plug_ra']
    dec = data[0].header['plug_dec']
    z = data[2].data['z'][0]
    plateid = data[0].header['plateid']
    mjd = data[0].header['mjd']
    fiberid = data[0].header['fiberid']

    q = QSOFit(lam, flux, err, z, ra=ra, dec=dec, plateid=plateid, mjd=mjd, fiberid=fiberid, path=path_ex)

    q.Fit(name=None, nsmooth=1, deredden=True, reject_badpix=False, wave_range=None, wave_mask=None,
          decompose_host=True, host_prior=False, decomp_na_mask=True, npca_gal=5, npca_qso=20, Fe_uv_op=True, poly=True, BC=False, rej_abs_conti=False,
          rej_abs_line=False,
          MCMC=False, plot_fig=False, save_fig=False, save_result=True,
          kwargs_plot={'save_fig_path': '.', 'broad_fwhm': 1200},
          save_fits_path=path_out, save_fits_name=None, verbose=False)

# Edit the directory before use
from multiprocessing import Pool # Use multiprocessing instead if you are running in a script!
import os, timeit, glob

if __name__ == '__main__':
    start = timeit.default_timer()

    files = glob.glob(os.path.join(path_ex, 'data/spec-*.fits'))

    pool = Pool(3)  # Create a multiprocessing Pool
    pool.imap(func=job, iterable=files)

    pool.close()  # Prevents adding more tasks
    pool.join()   # Waits for all jobs to finish 
    
    end = timeit.default_timer()
    print(f'Fitting finished in : {np.round(end - start)}s')