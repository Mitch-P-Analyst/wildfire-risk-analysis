#-- Packages --#

#--- Operational ---#
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os
import zipfile
import shutil
import geopandas as gpd
from shapely.geometry import Polygon

#-- Directories --#
REPO_ROOT = Path(__file__).resolve().parent.parent
data_dir = REPO_ROOT / 'data/'
processed_dir = data_dir / 'processed/'
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))



#-- Helper Functions --#


# Unzip all Shapefiles
def unzip_to_folder(zip_path, extract_to):              # Unzip NBAC files to destination
    """
    Unzips a ZIP archive into a specified directory.
    """
    extract_to = Path(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)                  # Read SHP to destination folder

    macosx_folder = extract_to / '__MACOSX'
    if macosx_folder.exists():
        shutil.rmtree(macosx_folder)


#-- Constants --#


zippaths = Path(data_dir/'raw/zips')                    # ZIPs folders
zipfolders = list(zippaths.glob('*.zip'))               # Select all .ZIP


#-- Process --#

print('Unzipping NBAC shapefiles...')
for folder in zipfolders:
    unzip_to_folder(folder,processed_dir/'shapefiles'/str(folder.name)[:-4])    # Retain name indentity
    print(f'NBAC Wildfires Year: {(str(folder.name)[5:9])} Shapefiles opened')

print(f'Target folder destination: {processed_dir/'shapefiles'} \n')




print('Opening all shapefiles...')
#--- Open all Shapefiles ---#
print(f'Appending into singular dictionary...')
all_gdfs_dct = {}   # Store in dictionary

for folder in (processed_dir / "shapefiles").iterdir(): # shapefiles directory
    if folder.is_dir():
        shp = next(folder.glob("*.shp"), None)          # specific shapefiles
        if shp:
            name = folder.name
            all_gdfs_dct[name] = gpd.read_file(shp)     # Geopandas read

print('All shapefiles opened. \n')





#--- Assess each shapefile's (key) column structure ---#
print(f'Beginning Cleaning. \n')
# 1. Get a singular shapefile as the reference file

# Reference shapefile
reference_year = 2024
print(f'Utilise singular shapefile structure as reference guide. \n Referenced shapefile: Year {reference_year}')
    
# Acquire candidate reference file
candidate = [k for k in all_gdfs_dct.keys() if str(reference_year) in str(k)]

if not candidate:
    raise KeyError(f"No shapefile containing reference year {reference_year} found in all_gdfs_dct.")
if len(candidate) > 1:
    print(f"Multiple shapefiles containing reference year {reference_year} candidates found. Using the first: {candidate}")


ref_key = candidate[0]
# Use reference shapefile columns
ref_cols = set(all_gdfs_dct[ref_key].columns)

# 2. Create a dictionary for any irregular shapefiles 
irregular = {}

# 3. Mark columns that exist in each GeoDataFrame
print(f'Comparing shapefile structure to reference file...')
for name, gdf in all_gdfs_dct.items():
    cols = set(gdf.columns)

# 4. Assess column structure
    missing_from_this = sorted(ref_cols - cols)
    extra_in_this     = sorted(cols - ref_cols)
# 5. Identify irregular shapefiles
    if missing_from_this or extra_in_this:
        irregular[name] = {
            f"missing_vs_{reference_year}": missing_from_this,
            f"extra_vs_{reference_year}": extra_in_this
        }

if not irregular:
    print(f"All shapefiles match the {reference_year} reference structure: {ref_key}")
else:
    print(f"{len(irregular)} shapefile(s) differ from {reference_year} reference: {ref_key}\n")
    for name, diffs in irregular.items():
        print(f"- {name}")
        if diffs[f"missing_vs_{reference_year}"]:
            print(f"   missing: {diffs[f'missing_vs_{reference_year}']}")
        if diffs[f"extra_vs_{reference_year}"]:
            print(f"   missing: {diffs[f'missing_vs_{reference_year}']}")
        if diffs[f"extra_vs_{reference_year}"]:
            print(f"   extra:   {diffs[f'extra_vs_{reference_year}']}")
        print()

    raise ValueError(f"Irregular column structures detected vs {reference_year}. See details above.")



#--- Singular GDF Location ---#

print(f'\nProducing singular GDF..')


# 1. Pick a reference CRS from the first GeoDataFrame
first_gdf = next(iter(all_gdfs_dct.values()))
target_crs = first_gdf.crs

gdfs_to_concat = []

for name, gdf in all_gdfs_dct.items():
    # reproject if needed
    if gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)
    
    # either keep only columns shared by all:
    # gdf = gdf[common_cols]

    # or, if you’re okay with missing columns being NaN, skip that line
    gdfs_to_concat.append(gdf)

# 2. Stack them vertically
fires_all_years = gpd.GeoDataFrame(
    pd.concat(gdfs_to_concat, ignore_index=True),
    crs=target_crs
)

# 3. Combine

combined = {"NBAC_all_years": fires_all_years}
all_gdf_df = combined["NBAC_all_years"]
print(f'Singular GDF produced.')

print(f'All fire geometries dataframe shape: {all_gdf_df.shape} \n')

# print(f'Null Values: \n{all_gdf_df.isnull().sum()}\n')


#--- Geodataframe Cleaning ---#

# 1. Create copy
all_gdf_df = all_gdf_df.copy()

# 2. rename and format columns 
col_names = {
    'Shape_Leng' : "shape_length",
    "FIRECAUS": "CAUSE",
    "NFIREID": "FIREID",
    'ADMIN_AREA':'prov_terr'
}

all_gdf_df = all_gdf_df.rename(columns=col_names)
print(f'Columns formatted')


# 3. lower-case all column names in one line
all_gdf_df.columns = all_gdf_df.columns.str.lower()

# 4. reassign datatypes
all_gdf_df['year'] = all_gdf_df['year'].astype(int)
all_gdf_df['fireid'] = all_gdf_df['fireid'].astype(int)
all_gdf_df['hs_sdate'] = all_gdf_df['hs_sdate'].astype('datetime64[ns]')
all_gdf_df['hs_edate'] = all_gdf_df['hs_edate'].astype('datetime64[ns]')
all_gdf_df['ag_sdate'] = all_gdf_df['ag_sdate'].astype('datetime64[ns]')
all_gdf_df['ag_edate'] = all_gdf_df['ag_edate'].astype('datetime64[ns]')
all_gdf_df['capdate'] = all_gdf_df['capdate'].astype('datetime64[ns]')

print(f'Column datatypes assigned.')
cols = ['gid', 'fireid', 'year', 'prov_terr', 'natpark', 'adj_ha','cause', 'geometry']
print(f'Columns selected for further analysis: \n {cols}')
Canfires_simple = all_gdf_df[cols].copy()

# Identify year range (cast to int to avoid "2014.0")
Canfires_year_min = int(Canfires_simple['year'].min())
Canfires_year_max = int(Canfires_simple['year'].max())

# Reproject to WGS84 for GeoJSON / broad compatibility
print('Reprojecting CRS...')
Canfire_4326 = Canfires_simple.to_crs(epsg=4326)
print(f' Reprojected CRS for GeoJSON export: {Canfire_4326.crs}')

print(f'\nCleaning complete. \n')
#--- Canada Fires Export ---#
print(f'Beginning Export procedure.')
# Output folder
out_dir = processed_dir / "Canada_fires"
out_dir.mkdir(parents=True, exist_ok=True)

# ---- GeoJSON export ----
Canfires_path_geojson = out_dir / f"Canada_fires_{Canfires_year_min}_{Canfires_year_max}.geojson"
print('Exporting Canadian fires GeoJSON...')

try:
    Canfire_4326.to_file(Canfires_path_geojson, driver="GeoJSON")
    print(f'GeoJSON export successful: {Canfires_path_geojson}')
except Exception as e:
    raise RuntimeError(f'Canadian fires GeoJSON failed to export: {e}')

# ---- Shapefile export ----
Canfires_path_shp = out_dir / f"Canada_fires_{Canfires_year_min}_{Canfires_year_max}.shp"
print('Exporting Canadian fires Shapefile...')

try:
    Canfire_4326.to_file(Canfires_path_shp, driver="ESRI Shapefile")
    print(f'Shapefile export successful: {Canfires_path_shp}')
except Exception as e:
    raise RuntimeError(f'Canadian fires Shapefile failed to export: {e}\n')

print('Py file complete.')
