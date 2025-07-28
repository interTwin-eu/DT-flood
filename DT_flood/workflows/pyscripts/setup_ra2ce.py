"""Script to setup RA2CE model."""

import argparse
from pathlib import Path
from shutil import copy, rmtree

import geopandas as gpd
import numpy as np
import osmnx as ox
import xarray as xr
from rasterio.features import rasterize
from xrspatial import zonal_stats

from DT_flood.utils.data_utils import download_single, download_tiled_data
from DT_flood.utils.ra2ce_utils import setup_base_folder


def _set_spatial_ref(ds):
    return ds.set_coords(("spatial_ref"))


parser = argparse.ArgumentParser()

parser.add_argument("--regionfile")
parser.add_argument("--popdata", default="worldpop")

args = vars(parser.parse_args())

ra2ce_root = Path.cwd() / "ra2ce"
region = gpd.read_file(args["regionfile"])
pop_scope = args["popdata"]

datafolder = Path.cwd() / "data"
datafolder.mkdir(exist_ok=True)

outlist = download_tiled_data(dataset=pop_scope, bbox=region.total_bounds)
pop_data = xr.open_mfdataset(outlist, preprocess=_set_spatial_ref)
pop_data.to_netcdf(datafolder / "pop.nc")

agg_fn = download_single(filename="gadm_ADM_4.gpkg", rucio_scope="wtromp")
agg_fn.rename(datafolder / agg_fn.name)

# Clean up rucio downloads
rmtree(Path.cwd() / "wtromp")

setup_base_folder(ra2ce_root)
copy(args["regionfile"], ra2ce_root / "static" / "network" / "map.geojson")

# Setup origin points
print("Creating Origin points")
agg = gpd.read_file(datafolder / agg_fn.name)
shapes = list(enumerate(agg["geometry"].values))
shapes = [(t[1], t[0] + 1) for t in shapes]

# convert xr.dataset to xr.dataarray
# assumed that dataset contains only single variable
pop_data = pop_data.to_dataarray().squeeze()

print("Rasterize to population data")
rasterized = rasterize(
    shapes=shapes,
    out_shape=pop_data.shape,
    transform=pop_data.raster.transform,
    all_touched=True,
)
rasterized = xr.DataArray(rasterized, coords={"y": pop_data.y, "x": pop_data.x})

zonal_out = zonal_stats(
    rasterized,
    pop_data.load(),
    stats_funcs=["sum"],
    nodata_values=np.nan,
)
zonal_out = zonal_out.drop(0)

print("Export origin points")
origins = gpd.GeoDataFrame(data=zonal_out, geometry=agg.geometry.centroid).dropna()
origins = origins.rename(columns={"sum": "POPULATION", "zone": "OBJECT ID"})
origins = origins.clip(region)
origins["category"] = "origin"
origins.to_file(ra2ce_root / "static" / "network" / "origins.gpkg", driver="GPKG")

# Setup Destination points
print("Setup Destination points")
print("Download OSM features")
feats = ox.features_from_polygon(region.geometry[0], tags={"amenity": ["hospital"]})

print("Export destination points")
dest = feats.reset_index()[["osmid", "amenity", "geometry"]]
dest = dest.rename(columns={"amenity": "category"})
dest["geometry"] = dest["geometry"].centroid

dest.to_file(ra2ce_root / "static" / "network" / "destinations.gpkg", driver="GPKG")
