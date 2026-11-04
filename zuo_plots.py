import csv
from pathlib import Path

from astropy.io import fits
import matplotlib.pyplot as plt


# Converted from the SDSS/FITS-redshift rest frame into the Zuo-paper
# rest frame: lambda_zuo = lambda_fits * (1 + z_fits) / (1 + z_zuo).
REST_FRAME_MASKS = {
    '0401': [(1535.361, 1538), (1539,1540.5), (1544.299, 1545.789), (1547.278, 1549.265)],
    '0725': [(1580.850, 1583.841), (1584.837, 1588.824)],
    '0731': [(1539.771, 1542.776), (1547.785, 1550.791)],
    '2608': [(1536.913, 1542.936)],
    '3683': [(1533, 1538)],
    '2825': [(1539.5, 1541.5)],
    '3699': [(1526.811, 1531.822)],
    '3804': [(1504.639, 1508.591), (1526,1527.5), (1546.1,1547.5), (1548.603, 1552.555)],
    '4206': [(1559.599, 1562.098), (1563.597, 1565.596), (1566.595, 1570.093)],
    '4604': [(1510.138, 1512.140), (1534.172, 1536.675), (1538, 1541.182), (1590.251, 1593.255)],
    '5496': [(1529.493, 1531.490)],
}


def get_spectrum_prefix(file_path):
    """Return the plate/prefix from names such as spec-0401-51788-0500."""
    name_parts = file_path.stem.split("-")
    return name_parts[1] if name_parts[0] == "spec" else name_parts[0]


project_root = Path(__file__).parent
data_dir = project_root / "CIV_galaxy_spectra_targets" / "zuo_civ_data" / "base_specs"
target_csv = project_root / "Target_lists" / "zuo_targets_data.csv"
with target_csv.open(newline="") as handle:
    ZUO_REDSHIFTS = {
        Path(row["fits_path"]).name: float(row["z"])
        for row in csv.DictReader(handle)
    }

for file_path in data_dir.glob("*.fits"):
    with fits.open(file_path) as hdul:
        z = ZUO_REDSHIFTS[file_path.name]

        wavelength_obs = 10 ** hdul[1].data["loglam"]
        flux = hdul[1].data["flux"]
        wavelength_rest = wavelength_obs / (1 + z)
        mask_regions = REST_FRAME_MASKS.get(get_spectrum_prefix(file_path), [])

        plt.figure(figsize=(12, 6))
        for lower, upper in mask_regions:
            plt.axvspan(lower, upper, color="grey", alpha=0.35, zorder=0)

        # Keep every original spectrum pixel visible; the grey spans only
        # highlight where masks would be applied during fitting.
        plt.plot(wavelength_rest, flux, color="black", lw=0.7, zorder=2)
        plt.xlabel("Wavelength (Å)", fontsize=14)
        plt.axvline(1549, color="red", lw=1.2, label="C IV (1549 Å)")
        plt.ylabel("Flux (arbitrary units)", fontsize=14)
        plt.title("Quasar Spectrum", fontsize=16)
        plt.xlim(1500, 1700)
        plt.ylim(0, 100)
        plt.grid(alpha=0.3)
        plt.savefig(file_path.with_suffix(".pdf"), bbox_inches="tight")
        plt.close()
