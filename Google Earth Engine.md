# Google Earth Engine

## Knowledge & Preparation

| **Common Functions**                      | **Purpose**                                                 |
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


| **Code Snippets/Functions**                       | **Description**
|---------------------------------------------------|-------------------------------------------------------------|
| `ee.Geometry.Rectangle([xmin, ymin, xmax, ymax])` | [west, south, east, north] coordinates for Area Of Interest |
|
|
|



