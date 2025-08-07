# Google Earth Engine & Geemapp

**WATCH ME**

QiuSheng Wu Earth Engine & Geemap Seminar 
https://www.youtube.com/watch?v=swjQEE5jpgE&list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3&ab_channel=OpenGeospatialSolutions


## Knowledge & Preparation

| **Geemap Common Functions**               | **Purpose**                                                 |
| ----------------------------------------- | ----------------------------------------------------------- |
| `geemap.map()`                            | Produces interactive map                                    |
| `basemap()`                               | Basemap style `hyrbid, roadmap, OpenTopoMap` 405 options    |
| `add_tile_layer()`                        | Custom interactive map layer `url=` `name=` `attribution=`  |
|                                           |                                                             |
|                                           |                                                             |
|                                           |                                                             |
|                                           |                                                             |
|                                           |                                                             |
|                                           |                                                             |
|                                           |                                                             |




| **Earth Engine Common Functions**         | **Purpose**                                                 |
| ----------------------------------------- | ----------------------------------------------------------- |
| `ee.Initialize()`                         | Authenticates and connects to GEE                           |
| `ee.Geometry.*`                           | Create spatial areas (e.g. `Rectangle`, `Point`, `Polygon`) |
| `ee.ImageCollection()`                    | Loads a dataset (e.g. MODIS, Landsat, Sentinel)             |
| `.filterBounds(geometry)`                 | Filters images that intersect your AOI                      |
| `.filterDate('YYYY-MM-DD', 'YYYY-MM-DD')` | Temporal filter                                             |
| `.select('BANDS')`                        | Choose specific bands (e.g. NDVI, NIR, Red)                 |
| `.mean()` or `.median()`                  | Composite operation across time                             |
| `ee.Image()`                              | Access individual images                                    |
| `image.reduceRegion()`                    | Extract summary stats (e.g. mean NDVI) over an area         |
| `Export.image.toDrive()`                  | Export imagery to your Google Drive                         |


| **Earth Engine Code Snippets/Functions**          | **Description**                                             |
|---------------------------------------------------|-------------------------------------------------------------|
| `ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])` | [west, south, east, north] coordinates for Area Of Interest |
|                                                   |                                                             |
|                                                   |                                                             |

### DataTypes

Earth Engine Objects are server-side objects. As in they are not stored on your local computer, always in the 'cloud'

- Earth Engine Datatypes

    - Image 
        - The fundamental `Raster` type in Earth Engine
        - `Raster` data in EE are stored as Images
            - Images are composed of one or more **bands**. Each band has its own;
                - Name
                - Data Type
                - Scale
                - Mask
                - Projection

                Also Properties/Metadata

    - Image Collection
        - A Stack or Time Series of of images

    - Geometry
        - The fundamental `Vector` type in Earth Engine

    - Feature
        - A Geometry with attributes

    - Feature Collection
        - A set of features

Assign your acessed datatype to a variable

#### Image Datatype Example
- `image` = ee.Image('Date_Category_Value_01')

When loading a datatype, you identify your desired parameters
- Example
    - `visualisation_parameters` {
    'min' : 0,  <!-- `min` and `max` identify the range of values that shall be visualised. -->
    'max' : 6000,
    'pallete' : 'terrain',
    }

Assign your parameters and accessed data to the Map
- Example
    - Map.addlayer(`image`,`visualisation_parameters`, 'name')


#### Image Collection Datatype Example
Image Collection Data is a timeseries of images. Therefore, you can filter your timeseries of images to visualise & analyses by specific criteria

- `collection` = (ee.ImageCollection( 'Copernicus/S2_SR')
                .filterdate('2021-01-01','2021-12-31')
                .filter(ee.Filter.lt(`CLOUDY_PIXEL_PERCENTAGE`, 5))
                )
- `image` = `collection`.median()
    - In this situation, from a timeseries of images, you can selected for the 'median' value of all images.
    - I believe this criteria can be modified, but in this example, satilte imargery varys by brightness, so have filtered out all 'cloudy' data images, 'dark' data images, to find the **median** day visual

    - We have also filtered further by specifying images where `CLOUDY_PIXEL_PERCENTAGE` below 5%.
        - Therefore, Median() value of this filter

- `visualisation_parameters`{
    `min`: 0,
    `max`: 1000,
    `bands`: ['B4','B1','B5'],
    } 

- Map.set_center(**coordinates**)
- Map.addlayer(`image`, `visualisation_parameters`, **name**)





## Earth Engine Docs
Official API reference:
https://developers.google.com/earth-engine/apidocs

Getting started:
https://developers.google.com/earth-engine/guides/python_install

Geometry tools (like .Rectangle):
https://developers.google.com/earth-engine/geometry_visualization

## Datasets Search
Explore and find other datasets:

https://developers.google.com/earth-engine/datasets

Example searches:
- NDVI
- FIRMS fire data

## geemap GitHub & Tutorials
GitHub: https://github.com/giswqs/geemap

Jupyter Notebook Examples: https://geemap.org/notebooks

Full Documentation: https://geemap.org

## Tutorials
Excellent Earth Engine Python tutorials:
https://developers.google.com/earth-engine/tutorials

geemap tutorial series by the author (Qiusheng Wu):
https://www.youtube.com/watch?v=h0pz3S6Tvx0&ab_channel=OpenGeospatialSolutions

QiuSheng Wu Earth Engine & Geemap Seminar 
https://www.youtube.com/watch?v=swjQEE5jpgE&list=PLAxJ4-o7ZoPccOFv1dCwvGI6TYnirRTg3&ab_channel=OpenGeospatialSolutions
