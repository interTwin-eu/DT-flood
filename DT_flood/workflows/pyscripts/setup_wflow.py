"""Script to setup WFLOW model."""

import argparse
from pathlib import Path
from shutil import rmtree

import geopandas as gpd
import numpy as np
import xarray as xr
from hydromt.config import configread, configwrite
from hydromt.log import setuplog
from hydromt_wflow import WflowModel

from DT_flood.cfg import CFG_DIR
from DT_flood.utils.data_utils import (
    download_dataset,
    download_single,
    download_tiled_data,
    get_geodata,
)

parser = argparse.ArgumentParser()

parser.add_argument("--regionfile")
parser.add_argument("--sfincsroot")

parser.add_argument("--basindata", default="basin_atlas_v10")
parser.add_argument("--hydrodata", default="merit_hydro")
parser.add_argument("--riverdata", default="rivers_lin2019")
parser.add_argument("--lakedata", default="hydro_lakes")
parser.add_argument("--reservoirdata", default="hydro_reservoirs")
parser.add_argument("--lulcdata", default="globcover")
parser.add_argument("--laidata", default="modis_lai")
parser.add_argument("--soildata", default="soilgrids")

args = vars(parser.parse_args())

# Unpack args

wf_root = Path.cwd() / "wflow"
region = gpd.read_file(args["regionfile"])
gauges_fn = Path(args["sfincsroot"], "gis", "src.geojson")
datafolder = Path.cwd() / "data"
datafolder.mkdir(exist_ok=True)
wf_config = CFG_DIR / "wflow_build.yml"
catalog_fn = CFG_DIR / "catalog.yml"

basin_scope = args["basindata"]
hydro_scope = args["hydrodata"]
river_scope = args["riverdata"]
lake_scope = args["lakedata"]
reservoir_scope = args["reservoirdata"]
lulc_scope = args["lulcdata"]
lai_scope = args["laidata"]
soil_scope = args["soildata"]

# Get basin data and find all relevant basins
basins = get_geodata(basin_scope)
bas_ids = basins.clip(region)["MAIN_BAS"].unique()
region_full = basins[basins["MAIN_BAS"].isin(bas_ids)]
region_full["geometry"].to_file(datafolder / "basins.gpkg")


def _set_spatial_ref(ds):
    return ds.set_coords(("spatial_ref"))


# Get hydrography data
outlist = download_tiled_data(dataset=hydro_scope, bbox=region_full.total_bounds)
ds_full = xr.open_mfdataset(outlist, preprocess=_set_spatial_ref)
# ds_full.raster.to_mapstack(root="data/hydrography")
ds_full["flwdir"] = ds_full.flwdir.astype(np.uint8)
ds_full.to_netcdf(datafolder / "hydrography.nc")
del ds_full
index_fn = download_single(filename=f"{hydro_scope}_index.gpkg", rucio_scope="wtromp")
index_fn.rename(datafolder / "hydrography_index.gpkg")

# Get river data
rivers = get_geodata(river_scope, bbox=region_full.total_bounds)
rivers.to_file(datafolder / "rivers.gpkg", driver="GPKG")
del rivers

# Get lake data
lakes_fn = download_dataset(lake_scope)
for file in lakes_fn:
    file.rename(datafolder / "lakes.gpkg")

# Get reservoir data
reser_fn = download_dataset(reservoir_scope)
for file in reser_fn:
    file.rename(datafolder / "reservoirs.gpkg")

# Get LULC data
globcover_fn = download_dataset(dataset=lulc_scope)
globcover_ncs = [file for file in globcover_fn if ".nc" in file.name]
globcover = xr.open_mfdataset(globcover_ncs)
# This line is globcover specific, TODO: find way to do this generically
globcover.rename({"GLOBCOVER_L4_200901_200912_V2": "lulc"}).to_netcdf(
    datafolder / "lulc.nc"
)

# Get LAI data
lai_fns = download_dataset(dataset=lai_scope)
lai_ncs = [file for file in lai_fns if ".nc" in file.name]
lai = xr.open_mfdataset(lai_ncs, combine="nested", concat_dim="dim0")
lai.to_netcdf(datafolder / "lai.nc")

# Get soildata
outlist = download_tiled_data(dataset=soil_scope, bbox=region_full.total_bounds)
ds_full = xr.open_mfdataset(
    outlist,
)
ds_full.to_netcdf(datafolder / "soilmaps.nc")
del ds_full

# Clean up rucio downloads
rmtree(Path.cwd() / "wtromp")

logger = setuplog("wflow_build", log_level=10)

# dc = DataCatalog(data_libs=[catalog_fn])
# dc.to_yml("catalog.yml")

opt = configread(wf_config)

# opt["setup_basemaps"].update(region={"basin": datafolder/"basins.gpkg"})
opt["setup_basemaps"].update(region={"basin": region})
opt["setup_gauges"].update(gauges_fn=gauges_fn)

wf = WflowModel(
    root=wf_root,
    mode="w+",
    logger=logger,
    # data_libs=["catalog.yml"]
)
wf.data_catalog.get_geodataframe(datafolder / "hydrography_index.gpkg")
wf.build(opt=opt)
configwrite(wf_root / "wflow_build.yml", opt)
