# src/download_nbac.py

from pathlib import Path
import re
import requests

# ---------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = REPO_ROOT / "data" / "raw"
RAW_ZIPS_DIR = RAW_DIR / "zips"

RAW_DIR.mkdir(parents=True, exist_ok=True)
RAW_ZIPS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Directory Download ZIP Files: {RAW_ZIPS_DIR}")
print(f"Directory Download Raw Files: {RAW_DIR}")

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
BASE_URL = "https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/"
YEARS = range(2018, 2025)   # adjust if you want more years

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------
def find_latest_zip_filename(html: str, year: int) -> str | None:
    """
    Find the latest NBAC_<year>_YYYYMMDD.zip in the index HTML.
    """
    pattern = rf"NBAC_{year}_\d{{8}}\.zip"
    matches = re.findall(pattern, html)
    if not matches:
        return None
    # If there were multiple, pick the lexicographically last (usually newest)
    return sorted(set(matches))[-1]


def find_latest_stats_filename(html: str) -> str | None:
    """
    Find the latest NBAC_summarystats_1972to2024_YYYYMMDD.xlsx-style filename.
    """
    pattern = r"NBAC_summarystats_\d{4}to\d{4}_\d{8}\.xlsx"
    matches = re.findall(pattern, html)
    if not matches:
        return None
    return sorted(set(matches))[-1]


def download_file(fname: str, destination: Path) -> None:
    """
    Download fname from BASE_URL into destination, if not already present.
    """
    url = BASE_URL + fname
    out_path = destination / fname

    if out_path.exists():
        print(f"Already have {fname}, skipping.")
        return

    print(f"Downloading {fname} ...")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    print(f"Saved to {out_path}")


def main() -> None:
    # Grab the index page once
    html = requests.get(BASE_URL, timeout=30).text

    # --- Yearly ZIPs ---
    for year in YEARS:
        zip_name = find_latest_zip_filename(html, year)
        if not zip_name:
            print(f"No NBAC zip found for {year}")
            continue
        print(f"Found {year} file: {zip_name}")
        download_file(zip_name, RAW_ZIPS_DIR)

    # --- Summary stats file ---
    stats_name = find_latest_stats_filename(html)
    if not stats_name:
        print("No NBAC summarystats file found")
    else:
        print(f"Found summary stats file: {stats_name}")
        download_file(stats_name, RAW_DIR)

    print("Canada National Burned Area Composite (NBAC) data acquired.")


if __name__ == "__main__":
    main()
