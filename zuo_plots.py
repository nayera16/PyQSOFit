from pathlib import Path

from astropy.io import fits
import matplotlib.pyplot as plt


data_dir = Path(__file__).parent / "CIV_galaxy_spectra_targets" / "zuo_civ_data"

for file_path in data_dir.glob("*.fits"):
    with fits.open(file_path) as hdul:
        data_spec = hdul[3].data
        z = hdul[2].data["Z"][0]

        wavelength_obs = 10 ** hdul[1].data["loglam"]
        flux = hdul[1].data["flux"]
        wavelength_rest = wavelength_obs / (1 + z)

        plt.figure(figsize=(12, 6))
        plt.plot(wavelength_rest, flux, color="black", lw=0.7)
        plt.xlabel("Wavelength (Å)", fontsize=14)
        plt.axvline(1549, color="red", lw=1.2, label="C IV (1549 Å)")
        plt.ylabel("Flux (arbitrary units)", fontsize=14)
        plt.title("Quasar Spectrum", fontsize=16)
        plt.xlim(1500, 1700)
        plt.ylim(0, 100)
        plt.grid(alpha=0.3)
        plt.savefig(file_path.with_suffix(".pdf"), bbox_inches="tight")
        plt.close()
