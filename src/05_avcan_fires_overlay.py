#-- Packages --#

#--- Operational ---#
import os
import sys 
import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
import json
import re
import geopandas as gpd

#--- Visualisations ---#
import plotly.express as px
import plotly.graph_objects as go

#-- Directories --#
REPO_ROOT = Path(__file__).resolve().parent.parent
data_dir = REPO_ROOT / 'data/'
processed_dir = data_dir / 'processed/'
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


#-- Helper Functions --#
def extract_max_year(path):
    """
    Identify shapefile with latest year of available data
    """
    years = re.findall(r"\d{4}", path.stem)
    return max(map(int, years)) if years else -1


#-- Files --#

# Avalanche Canada polygons (GeoJSON)
print(f'Loading Avalanche Canada (AvCan) regions shapefile...')
avcan_path = REPO_ROOT / "data/external/avalanche_canada/canadian_subregions.geojson"
avcan_shapes = gpd.read_file(avcan_path)
print(f" Avalanche Canada Regions loaded. {avcan_shapes.crs}\n")

# NBAC / BC fire perimeters 
fires_dir = REPO_ROOT / "data/processed/Canada_fires"
shp_files = list(fires_dir.glob("*.shp"))

if not shp_files:
    raise FileNotFoundError(f"No shapefiles found in {fires_dir}\n")

fires_path = max(shp_files, key=extract_max_year)

print(f"Loading latest Canada fires shapefile... \n File name: {fires_path.name}")
canada_fires = gpd.read_file(fires_path)
print(f" National Canada Fires loaded. {canada_fires.crs}\n")


# Stats Canada Province / Territories boundaries
print(f'Loading Stats Canada Province + Territory boundaries shapefile...')
provinces = gpd.read_file(REPO_ROOT / "data/external/stats_canada/boundaries/lpr_000b21a_e.shp")
print(f" Canadian Province / Territory boundaries loaded. {provinces.crs}\n")



#-- Aggregations --#

# AvCanada Ski Regions
print('Isolate all AvCan regions.')
avcan_clean = avcan_shapes.copy()
print('AvCan column cleaning')
colnames = {
    'polygon_name':'subregion',
    'reference_region':'region'
}
avcan_clean = avcan_clean.rename(columns=colnames)
regions = avcan_clean[["region","subregion", "geometry"]]   # adjust column names as needed


print("Classifying AvCan subregions to Canadian Province / Territory...")

# Compute both layers into projected CRS
regions_proj   = regions.to_crs(3347)
provinces_proj = provinces.to_crs(3347)         # (StatsCan provinces are originally 3347)


print(' Joined by subregion boundaries within province/territory boundary.')
# Join AvCan region to province by shapefile boundaries across centroids
regions_with_admin = gpd.sjoin(
    regions_proj,
    provinces_proj[["PRENAME", "geometry"]],   # English name
    how="left",
    predicate="within"
).drop(columns="index_right")



regions_with_admin = regions_with_admin.rename(columns={"PRENAME": "prov_terr"})

regions_with_admin = regions_with_admin.drop(columns="geometry")
regions_with_admin = regions.merge(
    regions_with_admin[["region", "subregion", "prov_terr"]],
    on=["region", "subregion"],
    how="left"
)


print('\nOverlaying Canadian fires with respective AvCan subregions..')
canada_fires=canada_fires.drop(columns="prov_terr")
# Overlay BcFires to respective AvCanada Ski Regions
print('Splitting fires across AvCan subregions...')
fire_stats = gpd.overlay(
    canada_fires,
    regions_with_admin,
    how="intersection"   # intersection of fire and region polygons. Cutting fires by region borders
)
print(f' Overlay complete.')


# Make sure we use a projected CRS in metres for area calc
if fire_stats.crs.is_geographic:  # e.g. EPSG:4326
    fire_stats = fire_stats.to_crs("EPSG:3978")  # Canada Lambert as an example

print(f'''Convert fires_region variable CRS type to projected coordinates.
    Projected CRS type: {fire_stats.crs} (metres)
    Projected CRS name: {fire_stats.crs.name}\n
''')


print('Calculating area burned (ha) for each AvCan subregion split fire.')
# Create hectare area for each AvCanada Ski Region
fire_stats["subreg_ha"] = fire_stats.geometry.area / 10_000
fire_stats = fire_stats.rename(columns={'adj_ha':'tot_adj_ha'})
print(f' Individual fire per region burn = fire.geometry.area / 10_000 = "subreg_ha')

print(f' NBAC Total Region adjusted burn = "tot_adj_ha"\n')

print(f'Individual Fire Statistics DF complete. \n')



#--- AvCan Fires Exports ---#
print(f'Beginning Export procedure.')

# Identify year range (cast to int to avoid "2014.0")
AvCan_fires_year_min = int(fire_stats['year'].min())
AvCan_fires_year_max = int(fire_stats['year'].max())


# Output folder
out_dir = processed_dir / 'avalanche_canada/'
out_dir.mkdir(parents=True, exist_ok=True)

# ---- GeoJSON export ---- #
AvCan_fires_path_geojson = out_dir / f"AvCan_fires_{AvCan_fires_year_min}_{AvCan_fires_year_max}.geojson"
print('Exporting AvCan fires GeoJSON...')

try:
    fire_stats.to_file(AvCan_fires_path_geojson, driver="GeoJSON")
    print(f'AvCan GeoJSON export successful: {AvCan_fires_path_geojson}')
except Exception as e:
    raise RuntimeError(f'AvCan fires GeoJSON failed to export: {e}')

# ---- Shapefile export ---- #
AvCan_fires_path_geojson = out_dir / f"AvCan_fires_{AvCan_fires_year_min}_{AvCan_fires_year_max}.shp"
print('Exporting AvCan fires Shapefile...')

try:
    fire_stats.to_file(AvCan_fires_path_geojson, driver="ESRI Shapefile")
    print(f'Shapefile export successful: {AvCan_fires_path_geojson}')
except Exception as e:
    raise RuntimeError(f'AvCan fires Shapefile failed to export: {e}\n')

#--- AvCan Regions Export ---#

# ---- GeoJSON export ---- #
AvCan_regions_path_geojson = out_dir / f"AvCan_cleaned_subregions.geojson"
print('Exporting AvCan subregions GeoJSON...')

try:
    avcan_clean.to_file(AvCan_regions_path_geojson, driver="GeoJSON")
    print(f'AvCan cleaned subregions GeoJSON export successful: {AvCan_regions_path_geojson}')
except Exception as e:
    raise RuntimeError(f'AvCan cleaned subregions GeoJSON failed to export: {e}')


print('\nPy file complete.')
