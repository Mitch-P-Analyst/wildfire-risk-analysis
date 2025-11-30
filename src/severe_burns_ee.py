"""
Generate high-severity (dNBR ≥ 0.66) skiable patches for each fire,
mirroring the current Earth Engine JS logic.

- One export per (subregion, fireYear)
- Uses Brandywine fires asset as in your JS code
"""

import ee
import math
import os
import sys 
from pathlib import Path
import geopandas as gpd
import re
import geemap

# ---------------------------------------------------------------------
# INITIALISE EARTH ENGINE
# ---------------------------------------------------------------------

# Confirm authentication
ee.Authenticate(auth_mode='notebook')
print("Authentification:" ,ee.Authenticate())

# If Authentication issue, force in CLI
    # earthengine authenticate --quiet --force

# Initialize the Earth Engine module.
google_project = "wildfire-canada-475322"
ee.Initialize(project=str(google_project))
print("Initialized:", ee.data._credentials is not None, f"with {google_project}")
print(f"Initialized With Google Project {google_project}")


# Print current EE version
print("Earth Engine Version: ",ee.__version__)

# Test data access
print("Data Access:", ee.Number(1).getInfo())
print('\n')



# ---------------------------------------------------------------------
# GLOBAL DATASETS: DEM, TERRAIN, SLOPE, ASPECT
# ---------------------------------------------------------------------

dem      = ee.Image("USGS/SRTMGL1_003")
terrain  = ee.Algorithms.Terrain(dem)
slope    = terrain.select("slope")    # degrees
aspect   = terrain.select("aspect")   # degrees from north

# 8-way aspect classification (same as your JS)
aspectCat = aspect.expression(
    "(d >= 337.5 || d < 22.5) ? 0" +    # N
    ": (d >= 22.5  && d < 67.5)  ? 1" + # NE
    ": (d >= 67.5  && d < 112.5) ? 2" + # E
    ": (d >= 112.5 && d < 157.5) ? 3" + # SE
    ": (d >= 157.5 && d < 202.5) ? 4" + # S
    ": (d >= 202.5 && d < 247.5) ? 5" + # SW
    ": (d >= 247.5 && d < 292.5) ? 6" + # W
    ": 7",                              # NW
    {"d": aspect},
).rename("aspect_cat")

aspectLabels = ee.List(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])

# ---------------------------------------------------------------------
# HELPER FUNCTIONS (same logic as in JS)
# ---------------------------------------------------------------------

#-- Helper Functions --#
def extract_max_year(path):
    """
    Identify shapefile with latest year of available data
    """
    years = re.findall(r"\d{4}", path.stem)
    return max(map(int, years)) if years else -1



def maskS2clouds(image):
    """Cloud + cirrus mask for Sentinel-2 SR (same QA60 logic as JS)."""
    qa = image.select("QA60")
    cloudBitMask = 1 << 10
    cirrusBitMask = 1 << 11

    cloud_free = qa.bitwiseAnd(cloudBitMask).eq(0)
    cirrus_free = qa.bitwiseAnd(cirrusBitMask).eq(0)
    mask = cloud_free.And(cirrus_free)

    return (
        image.updateMask(mask)
        .copyProperties(image, image.propertyNames())
    )


def addNBR(image):
    nbr = image.normalizedDifference(["B8", "B12"]).rename("NBR")
    return image.addBands(nbr).copyProperties(image, image.propertyNames())


def add_aspect_stats(ft):
    """Continuous mean aspect 0–360° for a polygon."""
    ft = ee.Feature(ft)
    geom = ft.geometry()

    aspectRad = aspect.multiply(math.pi / 180.0)

    sinMean = aspectRad.sin().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=30,
        maxPixels=1e8,
    ).get("aspect")

    cosMean = aspectRad.cos().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=30,
        maxPixels=1e8,
    ).get("aspect")

    meanRad = ee.Number(sinMean).atan2(ee.Number(cosMean))
    meanDeg = meanRad.multiply(180.0 / math.pi).add(360).mod(360)

    return ft.set({"aspect_mean_deg": meanDeg})


def add_cardinal_aspect(ft):
    """Dominant cardinal aspect (N, NE, …, NW) for a polygon."""
    ft = ee.Feature(ft)
    geom = ft.geometry()

    mode = ee.Number(
        aspectCat.reduceRegion(
            reducer=ee.Reducer.mode(),
            geometry=geom,
            scale=30,
            maxPixels=1e8,
        ).get("aspect_cat")
    ).round()

    domCardinal = aspectLabels.get(mode)
    return ft.set({"aspect_cardinal": domCardinal})


# ---------------------------------------------------------------------
# PER-FIRE PROCESSING FUNCTION (uses same names as JS)
# ---------------------------------------------------------------------


def make_process_fire_fn(bigPatchMask):
    """Return a function that processes a *single* fire using a shared bigPatchMask."""

    def process_fire(fire):
        fire = ee.Feature(fire)
        geom = fire.geometry()

        # Local big-patch mask just inside this fire
        localMask = bigPatchMask.clip(geom)

        # Vectorise big high-severity patches in this fire
        patches = localMask.selfMask().reduceToVectors(
            geometry=geom,
            scale=vectScale,
            geometryType="polygon",
            eightConnected=True,
            labelProperty="patch_id",
            maxPixels=1e7,
        )

        # Attach fire-level attributes
        def add_fire_attrs(p):
            p = ee.Feature(p)
            return p.set(
                {
                    "gid": fire.get("gid"),
                    "fireid": fire.get("fireid"),
                    "year": fire.get("year"),
                    "natpark": fire.get("natpark"),
                    "region": fire.get("region"),
                    "subregion": fire.get("subregion"),
                }
            )

        patches = patches.map(add_fire_attrs)

        # Terrain + slope stats per patch
        def add_terrain(p):
            p = ee.Feature(p)
            pGeom = p.geometry()

            a_m2 = pGeom.area(maxError=10)

            elevStats = dem.reduceRegion(
                reducer=ee.Reducer.minMax().combine(
                    reducer2=ee.Reducer.mean(), sharedInputs=True
                ),
                geometry=pGeom,
                scale=30,
                maxPixels=1e6,
            )

            slopeStats = slope.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    reducer2=ee.Reducer.stdDev(), sharedInputs=True
                ),
                geometry=pGeom,
                scale=30,
                maxPixels=1e6,
            )

            slopeMean = ee.Number(slopeStats.get("slope_mean"))
            slopeStd = ee.Number(slopeStats.get("slope_stdDev"))
            slopeMeanPct = (
                slopeMean.multiply(math.pi / 180.0).tan().multiply(100.0)
            )

            elev_min = elevStats.get("elevation_min")
            elev_max = elevStats.get("elevation_max")
            elev_relief = ee.Number(elev_max).subtract(ee.Number(elev_min))

            return p.set(
                {
                    "patch_area_m2": a_m2,
                    "patch_area_ha": a_m2.divide(1e4),
                    "elev_min_m": elev_min,
                    "elev_max_m": elev_max,
                    "elev_mean_m": elevStats.get("elevation_mean"),
                    "elev_relief_m": elev_relief,
                    "slp_mn_deg": slopeMean,
                    "slp_std_dg": slopeStd,
                    "slp_mn_pct": slopeMeanPct,
                }
            )

        patches = patches.map(add_terrain)

        # Aspect stats
        patches = patches.map(add_aspect_stats).map(add_cardinal_aspect)

        return patches

    return process_fire


# ---------------------------------------------------------------------
# MAIN FUNCTION: ONE (subName, fireYear) → START EXPORT TASK
# ---------------------------------------------------------------------


def run_subregion_year(subName, fireYear, fires_fc):
    """Process one (subregion, fireYear) and start an export task if patches exist."""
    print(f'\nBegin new Subregion + Year severe fire analysis.\n')
    fires = (
        fires_fc.filter(ee.Filter.eq("subregion", subName))
        .filter(ee.Filter.eq("year", fireYear))
    )

    n_fires = fires.size().getInfo()
    if n_fires == 0:
        print(f"[{subName} {fireYear}] No fires – skipping.")
        return

    print(f"[{subName} {fireYear}] Number of Fires:", n_fires)

    # Geometry to bound the Sentinel-2 search
    allGeom = fires.geometry()
    
    # Pre/post windows tied to the fire year (same as JS)
    preStart = ee.Date.fromYMD(fireYear - 1, 1, 1)
    preEnd = ee.Date.fromYMD(fireYear - 1, 12, 31)
    postStart = ee.Date.fromYMD(2025, 1, 1)
    postEnd = ee.Date.fromYMD(2025, 12, 31)

    # Format on the EE side, then pull to Python
    preStart_str  = preStart.format('YYYY-MM-dd').getInfo()
    preEnd_str    = preEnd.format('YYYY-MM-dd').getInfo()
    postStart_str = postStart.format('YYYY-MM-dd').getInfo()
    postEnd_str   = postEnd.format('YYYY-MM-dd').getInfo()

    print(f" Pre-fire window timeframe:  {preStart_str}  –  {preEnd_str}")
    print(f" Post-fire window timeframe: {postStart_str} –  {postEnd_str}")


    # Sentinel-2 collection
    print(f' Creating Sentinel-2 Composite')
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(allGeom)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 40))
        .map(maskS2clouds)
        .map(addNBR)
    )
    print('  Apply QA60 Cloud Masking. \n  Apply Normaliztion Burn Ratio Index')

    print(
        f" Sentinel-2 images after cloud filter: {s2.size().getInfo()} \n"
        f"  (Pre + Post fire windows built server-side)"
    )

    preColl = s2.filterDate(preStart, preEnd)
    postColl = s2.filterDate(postStart, postEnd)

    pre_count  = preColl.size().getInfo()
    post_count = postColl.size().getInfo()
    print(f"  Pre-window images: {pre_count}, Post-window images: {post_count}")

    if pre_count == 0 or post_count == 0:
        print(
            f"  [SKIP] {subName} {fireYear}: "
            f"   Pre/Post windows have no images "
            f"   (pre={pre_count}, post={post_count}).\n"
        )
        return



    pre = preColl.select("NBR").median()
    post = postColl.select("NBR").median()
    dNBR = pre.subtract(post).rename("dNBR")

    # High-severity mask & connected components
    highMask = dNBR.gte(highThr)                
    print(f' Mask dNBR for high threshold burn scars. \n  Burn Severity dNBR threshold = {highThr}')

    # boolean image: 1 where dNBR >= highThr, 0 elsewhere
    patchPix = highMask.connectedPixelCount(                
        maxSize=1024,           
        eightConnected=True,
    )

    # for each pixel in a high-severity patch, this holds the *size of that patch in pixels* (0 where not highMask) 
    pixelArea_m2 = vectScale * vectScale
    minPatchPixels = (
        ee.Number(minPatchHa).multiply(1e4).divide(pixelArea_m2)
    )

    print(
        f" Min patch pixels at {vectScale} m: "
        f" {minPatchPixels.getInfo():.1f}"
    )

    print(
    f" Building bigPatchMask: high-severity patches \n"
    f"   (dNBR ≥ {highThr}) with area ≥ {minPatchHa} ha \n"
    f"   ({minPatchPixels.getInfo():.1f} pixels at {vectScale} m)"
    )
    # keep only pixels that are BOTH:
        #   - high severity (highMask == 1)
        #   - belong to a connected patch whose size >= minPatchPixels
    bigPatchMask = highMask.updateMask(patchPix.gte(minPatchPixels))

    # Per-fire processing (returns collection of collections)
    process_fire = make_process_fire_fn(bigPatchMask)
    perFirePatches = fires.map(process_fire)

    # Flatten to one FeatureCollection
    skiablePatchesWithAspect = ee.FeatureCollection(perFirePatches).flatten()

    n_patches = skiablePatchesWithAspect.size().getInfo()
    print(f"  Total skiable patches: {n_patches}")

    if n_patches == 0:
        print(
            f"  No big severe patches for {subName} in {fireYear} – "
            "no export started."
        )
        return

    # Keep only the fields you care about (same as your JS select)
    exportPatches = skiablePatchesWithAspect.select(
        [
            "patch_id",
            "gid",
            "fireid",
            "year",
            "natpark",
            "region",
            "subregion",
            "patch_area_ha",
            "elev_min_m",
            "elev_max_m",
            "elev_mean_m",
            "elev_relief_m",
            "slp_mn_deg",
            "slp_mn_pct",
            "aspect_cardinal",
            "aspect_mean_deg",
        ]
    )

    desc = f"AvCan_{subName}_{fireYear}_big_severe_patches"
    print(f"  Starting export task: {desc}")

    task = ee.batch.Export.table.toDrive(
        collection=exportPatches,
        description=desc,
        folder=output_folder,   # a folder in Google Drive
        fileFormat="SHP",
    )
    task.start()


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

#-- Directories --#
REPO_ROOT = Path(__file__).resolve().parent.parent
data_dir = REPO_ROOT / 'data/'
processed_dir = data_dir / 'processed/'
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


subregion_list = ["Brandywine"]          # extend later if you like
year_list = list(range(2018, 2025))      # 2018–2024 inclusive

highThr   = 0.66     # dNBR threshold for “high severity”
vectScale = 30       # vectorisation scale (m)
minPatchHa = 6       # minimum patch area in hectares
output_folder = "AvCanSevereBurns"

# Avalanche Canada fires 
fires_dir = REPO_ROOT / "data/processed/avalanche_canada"
shp_files = list(fires_dir.glob("*.shp"))

if not shp_files:
    raise FileNotFoundError(f"No shapefiles found in {fires_dir}\n")

fires_path = max(shp_files, key=extract_max_year)

print(f"Loading AvCan fires shapefile... \n File name: {fires_path.name}")
AVCAN_FIRES = gpd.read_file(fires_path)
print(f" Avalanche Canada Fires loaded. {AVCAN_FIRES.crs}\n")

print(f'Compute AvCan Fires into Geographical CRS')
# Ensure WGS84 (lat/lon) for EE
AVCAN_FIRES_wgs = AVCAN_FIRES.to_crs(epsg=4326)
print(f'Avalanche Canada Fires transformed: {AVCAN_FIRES_wgs.crs}\n')

# --- GeoPandas -> Earth Engine FeatureCollection ---
print(f'Load AvCan Fires into Google Earth Engine as Feature Collection. \n Loading...')
AVCAN_FIRES_ASSEST_ID = "projects/wildfire-canada-475322/assets/AvCan_fire_2014_2024"
AvCan = ee.FeatureCollection(AVCAN_FIRES_ASSEST_ID)
print("EE FeatureCollection size:", AvCan.size().getInfo())

# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------


def main():
    # Use the global AvCan we created above
    for subName in subregion_list:
        for fireYear in year_list:
            try:
                run_subregion_year(subName, fireYear, AvCan)
            except Exception as e:
                # Keep going even if one combo fails
                print(f"[{subName} {fireYear}] ERROR:", e)


if __name__ == "__main__":
    main()
