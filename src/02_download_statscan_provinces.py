#-- Packages --#

from pathlib import Path
import requests
import zipfile

#-- Directories --#
REPO_ROOT = Path(__file__).resolve().parent.parent
IN_DIR = REPO_ROOT / "data" / "external" / "stats_canada"
OUT_DIR = REPO_ROOT / "data" / "external" / "stats_canada" / "boundaries"
OUT_DIR.mkdir(parents=True, exist_ok=True)

#-- Contsants --#
URL = (
    "https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/"
    "boundary-limites/files-fichiers/lpr_000b21a_e.zip"
)

ZIP_NAME = "lpr_000b21a_e.zip"
zip_path = IN_DIR / ZIP_NAME

#-- Helper Functions --#

def download_statscan_provinces():
    '''
    Download shapefile of Canadian provinces and territories
    '''
    if zip_path.exists():
        print(f"Zip already exists at {zip_path}, skipping download.")
    else:
        print(f"Downloading StatsCan provinces from {URL} ...")
        with requests.get(URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)
        print(f"Saved zip to {zip_path}")

    print("Extracting shapefile...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(OUT_DIR)
    print(f"Extracted to {OUT_DIR}")


#-- Run --#

if __name__ == "__main__":
    download_statscan_provinces()
