# Build a Delft-FIAT model for the FloodAdapt backend

This notebook demonstrates how to set up a Delft-FIAT model anywhere in the world ready to be used in FloodAdapt. As an example we will create a model for the city of Kingston upon Hull, UK, in the Humber delta. The relevant data will be taken from [OpenStreetMap (OSM)](https://www.openstreetmap.org) and the [global flood vulnerability datasets from JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC105688). Both the data sources and the region of interest (the model domain) can be changed according to the user's wishes.

*Disclaimer: The outcomes of this model are not validated*

## **Step 0**: Import required packages
First we need to import the necessary python packages.


```python
import os
import numpy as np
import xarray as xr
from hydromt_fiat.workflows.exposure_vector import ExposureVector
from hydromt_fiat.fiat import FiatModel
from hydromt.log import setuplog
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
from rasterio.features import rasterize
from xrspatial import zonal_stats
```

## **Step 1:** List Input Names
Here we list the input paths and names of some needed utilities:
- `model_name`: This is the name for the overall FloodAdapt folder where everything will be stored. Named after region of interest (in this case)
- `model_path`: The full path of the FloodAdapt model folder
- `fiat_root`: Path to folder parsed by FloodAdapt where FIAT model is stored.
- `fiat_logger_name`: Name for the FIAT logger
- `region_fn`: Path to geojson file of the region of interest. Used when building FIAT domain
- `data_catalog_fn`: Path to data_catalog yml file


```python
model_name = 'Humber'
#model_path = Path('/home/wotromp/InterTwin/FloodAdapt_database') / model_name
model_path = Path('/home/jovyan/work/Project') / model_name

fiat_root = model_path / Path('static/templates/fiat')

fiat_logger_name = "FIAT_logger"

#region_fn = model_path / 'HumberDelta_large.geojson'
region_fn = Path('/home/jovyan/work/Data/region') / 'HumberDelta_large.geojson'
#data_catalog_fn = Path('/home/wotromp/InterTwin/Data/Humber/data_catalog.yml')
data_catalog_fn = Path('/home/jovyan/work/Data/data_catalog.yml')

```

## **Step 2**: Initialize
In this step we initialize HydroMT-FIAT with the `model_folder`, `data_catalog`, and `logger` that we defined above.


```python
fiat_logger = setuplog(fiat_logger_name, log_level=10)

fiat = FiatModel(root=fiat_root, data_libs=[data_catalog_fn], mode='w+', logger=fiat_logger)
```

    2024-09-23 08:00:12,420 - FIAT_logger - log - INFO - HydroMT version: 0.9.4
    2024-09-23 08:00:12,422 - FIAT_logger - data_catalog - INFO - Parsing data catalog from /home/jovyan/work/Data/data_catalog.yml
    2024-09-23 08:00:12,441 - FIAT_logger - log - DEBUG - Appending log messages to file /home/jovyan/work/Project/Humber/static/templates/fiat/hydromt.log.
    2024-09-23 08:00:12,441 - FIAT_logger - model_api - INFO - Initializing fiat model from hydromt_fiat (v0.3.2).


## **Step 3a:** Configure model - Setup Region
Build the model domain with the geojson file specified earlier. We also need to indicate the country and continent the model domain is in.


```python
print(region_fn)
```

    /home/jovyan/work/Data/region/HumberDelta_large.geojson



```python
region = gpd.read_file(region_fn)

continent = 'Europe'
country = 'United Kingdom'
```


```python
region.crs
```




    <Geographic 2D CRS: EPSG:4326>
    Name: WGS 84
    Axis Info [ellipsoidal]:
    - Lat[north]: Geodetic latitude (degree)
    - Lon[east]: Geodetic longitude (degree)
    Area of Use:
    - name: World.
    - bounds: (-180.0, -90.0, 180.0, 90.0)
    Datum: World Geodetic System 1984 ensemble
    - Ellipsoid: WGS 84
    - Prime Meridian: Greenwich



## **Step 3b:** Configure model - Configure input data

Next, we need to specify properties of the various dataset. For the vulnerability and exposure data HydroMT-FIAT needs the names and unit of the datasets. The names should correspond to the names (keys) in the data catalog except from the OSM data, which is accessed with the [OSMnx Python package](https://geoffboeing.com/publications/osmnx-complex-street-networks/). Should you wish to use different data sources, *make sure to update the data catalog*. For the output data, we need to specify the output file names and where to store them. The parameter names below are parsed by the model builder, so they should not be changed.

**Vulnerability**
- `vulnerability_fn`: the source name of the vulnerability curve dataset as defined in the HydroMT-FIAT global data catalog. In this example, we use the JRC global damage curves.
- `vulnerability_identifiers_and_linking_fn`: the source name of the *occupancy type-vulnerability curves* linking table as defined in the HydroMT-FIAT data catalog. In this example, we use the default table for linking the OSM land use classese to the JRC damage curves (i.e., the assets classified as residential links to the residential vulnerability curves of JRC).
- `unit`: the unit of the vulnerability curves. The JRC curves are in meters.

**Exposure**
- `asset_locations`: the source name of the location and (optionally) geometry data of the assests for which damages will be calculated. In this example, the building footprints from OSM are used.
- `occupancy_type`: the source name of the occupancy type data to classify the assets. In this example, the land use data from OSM is used.
- `max_potential_damage`: the source name of the maximum potential damage values data. In this example, the JRC maximum damage values are used.
- `ground_floor_height`: the height of the ground floor of all assets, in the same `unit`
- `unit`: the unit of the exposure data

**Output**
- `output_dir`: the name of the output directory
- `output_csv_name`: the name of the output CSV
- `output_vector_name`: the name of the vector output file(s)

*Note: The unit names are parsed by FloodAdapt. See FloodAdapt's UnitfulValue for correct formatting*


```python
### Setup vulnerability parameters ###
vulnerability_fn = "jrc_vulnerability_curves"
vulnerability_identifiers_and_linking_fn = "jrc_vulnerability_curves_linking"
unit = "meters"

### Setup exposure parameters ###
asset_locations = "OSM"
occupancy_type = "OSM"
max_potential_damage = "jrc_damage_values"
ground_floor_height = 0
ground_floor_height_unit = "meters"
damage_types = ['total']
ground_elevation_file = model_path / 'static' / 'dem' / "Humber_subgrid.tif"

### Setup output parameters ###
output_dir = "output"
output_csv_name = "output.csv"
output_vector_name = "spatial.gpkg"

### Setup Aggregation Zone parameters ###
# agg_area_folder = Path('c:/Repositories/DT-flood/Data/aggregation_zones')
# aggregation_area_fn = [agg_area_folder/"gadm41_GBR_3.shp"]
aggregation_area_fn = fiat.data_catalog['gadm_level1'].path
attribute_names = ["NAME_1"]
label_names = ["AdminZonesLevel1"]
```


```python
configuration = {
    "setup_output": {
        "output_dir": output_dir,
        "output_csv_name": output_csv_name,
        "output_vector_name": output_vector_name,
    },
    "setup_vulnerability": {
        "vulnerability_fn": vulnerability_fn,
        "vulnerability_identifiers_and_linking_fn": vulnerability_identifiers_and_linking_fn,
        "continent": continent,
        "unit": unit,
    },
    "setup_exposure_buildings": {
        "asset_locations": asset_locations,
        "occupancy_type": occupancy_type,
        "max_potential_damage": max_potential_damage,
        "ground_floor_height": ground_floor_height,
        "unit": ground_floor_height_unit,
        "country": country,
        "damage_types": damage_types,
        "ground_elevation_file": ground_elevation_file,
    },
    "setup_aggregation_areas": {
        "aggregation_area_fn": aggregation_area_fn,
        "attribute_names": attribute_names,
        "label_names": label_names,
    },
}
```

## **Step 4:** Build model

In this step we build the Delft-FIAT model. Depending on the extent of the model it can take some time to download the building footprints and land use data from OSM. During the building of the model, log messages display what is happening.

*Note that the model will not yet be written because of setting the write argument to False.*


```python
fiat.build(region={"geom": region}, opt=configuration, write=True)
```

    2024-09-23 08:00:22,291 - FIAT_logger - model_api - INFO - setup_region.region: {'geom':                                             geometry
    0  POLYGON ((-1.05682 53.82248, -1.05682 53.45678...}
    2024-09-23 08:00:22,292 - FIAT_logger - basin_mask - DEBUG - Parsed region (kind=geom): {'geom': 'GeoDataFrame [-1.05681688 53.45678163  0.17432842 53.82248393] (crs = EPSG:4326)'}
    2024-09-23 08:00:22,295 - FIAT_logger - model_api - INFO - setup_output.output_dir: output
    2024-09-23 08:00:22,296 - FIAT_logger - model_api - INFO - setup_output.output_csv_name: output.csv
    2024-09-23 08:00:22,296 - FIAT_logger - model_api - INFO - setup_output.output_vector_name: spatial.gpkg
    2024-09-23 08:00:22,297 - FIAT_logger - model_api - ERROR - Default config file not found at /home/jovyan/work/Notebooks/data/fiat/settings.toml
    2024-09-23 08:00:22,297 - FIAT_logger - model_api - INFO - setup_vulnerability.vulnerability_fn: jrc_vulnerability_curves
    2024-09-23 08:00:22,298 - FIAT_logger - model_api - INFO - setup_vulnerability.vulnerability_identifiers_and_linking_fn: jrc_vulnerability_curves_linking
    2024-09-23 08:00:22,298 - FIAT_logger - model_api - INFO - setup_vulnerability.unit: meters
    2024-09-23 08:00:22,298 - FIAT_logger - model_api - INFO - setup_vulnerability.functions_mean: default
    2024-09-23 08:00:22,299 - FIAT_logger - model_api - INFO - setup_vulnerability.functions_max: None
    2024-09-23 08:00:22,300 - FIAT_logger - model_api - INFO - setup_vulnerability.step_size: None
    2024-09-23 08:00:22,300 - FIAT_logger - model_api - INFO - setup_vulnerability.continent: Europe



    ---------------------------------------------------------------------------

    FileNotFoundError                         Traceback (most recent call last)

    Cell In[28], line 1
    ----> 1 fiat.build(region={"geom": region}, opt=configuration, write=True)


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt/models/model_api.py:246, in Model.build(self, region, write, opt)
        244         write = False
        245     kwargs = {} if opt[method] is None else opt[method]
    --> 246     self._run_log_method(method, **kwargs)
        248 # write
        249 if write:


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt/models/model_api.py:188, in Model._run_log_method(self, method, *args, **kwargs)
        186     if v is not inspect._empty:
        187         self.logger.info(f"{method}.{k}: {v}")
    --> 188 return func(*args, **kwargs)


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt_fiat/fiat.py:201, in FiatModel.setup_vulnerability(self, vulnerability_fn, vulnerability_identifiers_and_linking_fn, unit, functions_mean, functions_max, step_size, continent)
        178 """Setup the vulnerability curves from various possible inputs.
        179 
        180 Parameters
       (...)
        197     means that all vulnerability functions are using mean).
        198 """
        200 # Read the vulnerability data
    --> 201 df_vulnerability = self.data_catalog.get_dataframe(vulnerability_fn)
        203 # Read the vulnerability linking table
        204 self.vf_ids_and_linking_df = self.data_catalog.get_dataframe(
        205     vulnerability_identifiers_and_linking_fn
        206 )


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt/data_catalog.py:1783, in DataCatalog.get_dataframe(self, data_like, variables, time_tuple, handle_nodata, provider, version, **kwargs)
       1780 else:
       1781     raise ValueError(f'Unknown tabular data type "{type(data_like).__name__}"')
    -> 1783 obj = source.get_data(
       1784     variables=variables,
       1785     time_tuple=time_tuple,
       1786     handle_nodata=handle_nodata,
       1787     logger=self.logger,
       1788 )
       1789 return obj


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt/data_adapter/dataframe.py:224, in DataFrameAdapter.get_data(self, variables, time_tuple, logger, handle_nodata)
        216 """Return a DataFrame.
        217 
        218 Returned data is optionally sliced by time and variables,
        219 based on the properties of this DataFrameAdapter. For a detailed
        220 description see: :py:func:`~hydromt.data_catalog.DataCatalog.get_dataframe`
        221 """
        222 try:
        223     # load data
    --> 224     fns = self._resolve_paths(variables=variables)
        225     self.mark_as_used()  # mark used
        226     df = self._read_data(fns, logger=logger)


    File /opt/conda/envs/DT-flood/lib/python3.11/site-packages/hydromt/data_adapter/data_adapter.py:407, in DataAdapter._resolve_paths(self, time_tuple, variables, zoom_level)
        404         fns_out.append(UPath(fn, **self.storage_options))
        406 if len(fns_out) == 0:
    --> 407     raise FileNotFoundError(f"No such file found: {path}{postfix}")
        409 return fns_out


    FileNotFoundError: No such file found: jrc_vulnerability_curves



```python
fiat.set_geoms(region.dissolve(), 'region')
fiat.region.set_crs(region.crs)
```

## **Step 5**: Inspect model
We now inspect the resulting exposure data and vulnerability curves that will be saved in the `fiat` instance.

### Exposure data
In the map below, the region and Secondary Object Type of the exposure objects are plotted. You can zoom in and see whether the data makes sense, perhaps using Google maps and/or streetview to validate the occupancy types.

*Note: In Delft-FIAT, exposure is defined with object footprints, lines or centroids. In this example we are only using the buildings extracted from the OSM data. This means we are not going to look into, e.g., farmland, roads, etc. but that is possible with Delft-FIAT.*


```python
fiat.exposure.get_full_gdf(fiat.exposure.exposure_db)
```


```python
fiat.region
```


```python
# Get the geodataframe with exposure data
gdf = fiat.exposure.get_full_gdf(fiat.exposure.exposure_db)

# Plot the region and the secondary object types of the exposure data
m = region.explore(name='Region', style_kwds={'color': 'black', 'fill': False})
m = gdf.explore(m=m, column='Secondary Object Type', name='Exposure types')
m
```

## **Step 6:** Write model

Finally, write the model in a folder structure appropriate for FloodAdapt. The right folders should be created automatically if our `model_path` and `fiat_root` are correct.


```python
fiat.write()

def tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")


tree(Path(fiat.root))
```

## **Step 7:** Double check exposure csv

The written exposure csv is probably missing the 'Ground Elevation' column, without which FIAT won't run. This column contains the average height of each building footprint. Here we calculate these numbers using xrspatial.zonal_stats. We will use the SFINCS subgrid as DEM.

We do need to be carefull with the zonal_stats output. This generally contains less entries than the number of shapes, due to either duplicate shapes (the csv contains the same footprint multiple times with different asset types) or geometries being rasterized to the same pixels. The rasterize output will only contain the results of the last occurence. We use the fact that in either case the rasterization is the same to copy the appropriate results for the shapes that didn't get rasterized.

*Note: hydromt also has a zonal_stats function but it's very slow*


```python
dem_path = model_path / 'static' / 'templates' / 'overland' / 'subgrid' / 'dep_subgrid.tif'
exposure_path = fiat_root / 'exposure' / 'exposure.csv'
buildings_path = fiat_root / 'exposure' / 'buildings.gpkg'
```


```python
# Make a GeoDataFrame of the exposure csv
exposure = pd.read_csv(exposure_path)
buildings = gpd.read_file(buildings_path)
gdf = buildings.merge(exposure, on="Object ID")
# gdf = gpd.GeoDataFrame(exposure.drop(columns='geometry'), geometry=gpd.GeoSeries.from_wkt(exposure['geometry']),crs="EPSG:4326")

```


```python
# Read in the DEM
dem = rasterio.open(dem_path)
```


```python
# Convert the exposure geometries to the dem crs
gdf = gdf.to_crs(dem.crs.data)
```


```python
# Create a list of geometries plus a label for rasterize
# The labels start at 1 since the label 0 is reserved for everything not in a geometry
# The order of each tuple is (geometry,label)
shapes = list(enumerate(gdf['geometry'].values))
shapes = [(t[1],t[0]+1) for t in shapes]
```


```python
rasterized = rasterize(
    shapes=shapes,
    out_shape=dem.shape,
    transform=dem.transform,
    all_touched=True
)
# zonal_stats needs xarrays as input
rasterized = xr.DataArray(rasterized)
```


```python
# Calculate the zonal statistics
zonal_out = zonal_stats(rasterized,xr.DataArray(dem.read(1)),
                        stats_funcs=['mean'],
                        nodata_values=np.nan)

# The zero label is for pixels not in a geometry so we discard them
zonal_out = zonal_out.drop(0)
```


```python
# Array storing the zonal means
# Store the calculated means at index corresponding to their label
zonal_means = np.full(len(shapes),np.nan)
zonal_means[[zonal_out['zone'].values-1]] = zonal_out['mean'].values

```


```python
# Add Ground Elevation column and get rid of nans in the appropriate way
exposure['Ground Elevation'] = zonal_means
exposure['Ground Elevation'].bfill(inplace=True)
```


```python
# Save to csv
exposure_path.unlink()
exposure.to_csv(exposure_path)
```

## **Step 8:** Manual aggregation zones

Should the setup_aggregation_areas fail when building the model, comment `setup_aggregation_areas` in the `config` dict and run the below cells. This will manually configure the aggregation areas with the data specified in `aggregation_area_fn`


```python
# Load in the exposure table and the aggregation zone file
# exposure_gdf = fiat.exposure.get_full_gdf(fiat.exposure.exposure_db)
exposure_path = fiat_root / 'exposure' / 'exposure.csv'
buildings_path = fiat_root / 'exposure' / 'buildings.gpkg'

exposure = pd.read_csv(exposure_path)
buildings = gpd.read_file(buildings_path)

exposure_gdf = buildings.merge(exposure, on="Object ID")
agg_zone_gdf = gpd.read_file(aggregation_area_fn[0], mask=region)
```


```python
# Merge the two
exposure_gdf = gpd.sjoin(
    exposure_gdf,
    agg_zone_gdf[["geometry", attribute_names[0]]],
    op="intersects",
    how="left"
)
```


```python
# Handle duplicate Object IDs
aggregated_gdf = exposure_gdf.groupby("Object ID")[attribute_names[0]].agg(list).reset_index()

exposure_gdf.drop_duplicates(subset="Object ID", keep="first", inplace=True)
exposure_gdf.drop(columns=attribute_names[0], inplace=True)
exposure_gdf = exposure_gdf.merge(aggregated_gdf, on="Object ID")
```


```python
# Clean up by renaming and deleting appropriate columns

def process_value(value):
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    elif isinstance(value, list) and len(value) > 1:
        return ", ".join(value)
    else:
        return value
    
exposure_gdf[attribute_names[0]] = exposure_gdf[attribute_names[0]].apply(process_value)

exposure_gdf.rename(columns={attribute_names[0]: f"Aggregation Label: {label_names[0]}"}, inplace=True)

if "index_right" in exposure_gdf.columns:
    del exposure_gdf["index_right"]
```


```python
# Save new exposure table
exposure_path.unlink()
exposure_gdf.to_csv(exposure_path)
```




