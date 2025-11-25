# Wildfire Counts in Avalanche Canada Regions (2014–2024)

In Progress.

## Overview
The current status of this geospatial analysis project is exploring how Canadian wildfire perimeters intersect Avalanche Canada forecast regions. The current phase focuses on building a clean, multi-year wildfire dataset from NBAC (National Burned Area Composite), overlaying it with Avalanche Canada subregions, and summarizing/visualizing wildfire counts by region.

### Project Status (so far)

- Download and combine NBAC wildfire perimeters into a single multi-year GeoDataFrame
- Clean and standardize schema (using 2024 as the canonical column set)
- Export a reduced, analysis-ready Canada-wide fires shapefile + GeoJSON
- Overlay fire perimeters with Avalanche Canada regions
- Produce wildfire count summaries and a choropleth map by forecast region

#### Next Steps:
- Use Google Earth Engine + Sentinel-2 to compute NBR / dNBR time series
- Quantify vegetation loss/recovery in high-fire AVCan regions
- Compare counts vs area burned, severity, and temporal trends
- Identify high burn scars in Avalanche Canada regions

### Data Sources
- NBAC – National Burned Area Composite (Canada wildfires)
    - Annual national wildfire perimeter products.
    - Used here for 2014–2024 fire polygons.
    - Fields include:
        - year, cause, admin area, adjusted hectares, etc.

- Avalanche Canada Forecast Regions
    - Subregion polygons used for avalanche forecasting and public hazard products.
    - Used as the spatial aggregation unit for wildfire counts.

- Statistics Canada – Provincial/Territorial Boundaries
    - Used for validating / assigning fire admin_area via overlays (BC, AB, YT, NL, etc.).
    - Ensures fires in National Parks (PC) are not dropped in provincial filtering.

- (Next Steps) Parks Canada National Parks + Provincial Parks polygons
    - Used to tag fires by park_type and park_name.

## Repository Structure
``` 
wildfire-risk-analysis/
│
├── data/
│   ├── external/
│   │   ├── nbac/                               # Raw NBAC downloads by year
│   │   ├── avalanche_canada/
│   │   │   └── canadian_subregions.geojson     # AVCan forecast regions
│   │   └── stats_canada/
│   │       └── boundaries/                     # Provincial/territory polygons
│   │
│   └── processed/
│       ├── Canada_fires/
│       │   ├── Canada_fires_2014_2024.geojson
│       │   └── Canada_fires_2014_2024.shp (+ sidecars)
│       ├── NBAC_Summary_Stats_Cleaned.xls      # Summary statistics of NBAC records
│       └── Shapefiles/
│           └── NBAC Unzipped shapefiles (+ sidecars)  
│
├── scripts/
│   ├── 01_download_nbac.py
│   ├── 02_download_statscan_provinces.py
│   ├── 03_clean_merge_nbac_shapefiles.py
│   └── 
│
├── notebooks/  
│   ├── 04_summary_stats_cleaning.ipynb         # To clean
│   ├── 05_AvCanRegions.IPYNB                   # Working notebook
│   └── 06_engine_earth.ipynb                   # Next steps
│
├── outputs/
│   ├── figures/
│   └── tables/
│
└── README.md
```

## Setup

### Environment

- Recommended Python stack:
    - geopandas
    - pandas
    - shapely
    - matplotlib / plotly

### Install
```
pip install -r requirements.txt
```

## Key Outputs
- Processed fires file
- Canada_fires_2014_2024.geojson
- Canada_fires_2014_2024.shp

- Fields retained for analysis:
    - gid 
        - unique fire perimeter id
    - fireid 
        - NBAC fire identifier
    - year
        - fire year
    - admin_area 
        - province/territory
    - natpark
        - NBAC park indicator (when available)
    - adj_ha
        - adjusted burned area (hectares)
    - cause
        - human/natural/unknown categories
    - geometry
        - fire perimeter polygon

- AVCan summary
    - Fire counts per Avalanche Canada region (2014–2024)
    - Choropleth map showing highest totals in interior BC and Alberta


Mitchell J. R. Palmer
Geospatial / Environmental Data Science
Portfolio + contact links in profile.