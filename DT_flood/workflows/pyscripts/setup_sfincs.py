"""Script to setup SFINCS model."""

import argparse
from pathlib import Path
from shutil import rmtree

import geopandas as gpd
import numpy as np
import xarray as xr
from hydromt.config import configread, configwrite
from hydromt.log import setuplog
from hydromt_sfincs import SfincsModel

from DT_flood.cfg import CFG_DIR
from DT_flood.utils.data_utils import (
    download_dataset,
    download_single,
    download_tiled_data,
    get_geodata,
)

parser = argparse.ArgumentParser()
# parser.add_argument("--modeldir")
parser.add_argument("--regionfile")

parser.add_argument("--res", type=float)
parser.add_argument("--subgridpixels", type=int)

parser.add_argument("--basindata", default="basin_atlas_v10")
parser.add_argument("--topodata", default="fabdem")
parser.add_argument("--bathydata", default="gebco")
parser.add_argument("--riverdata", default="merit_hydro")
# parser.add_argument("--riverdata", default="rivers_lin2019")
parser.add_argument("--lulcdata", default="globcover")
parser.add_argument("--infiltdata", default="gcn250")

args = vars(parser.parse_args())

# Unpack args
# sf_root = Path(args["modeldir"]/"overland")
sf_root = Path.cwd() / "overland"
region = gpd.read_file(args["regionfile"])
res = args["res"]
nr_subgrid_pixels = args["subgridpixels"]

basin_scope = args["basindata"]
topo_scope = args["topodata"]
bathy_scope = args["bathydata"]
river_scope = args["riverdata"]
lulc_scope = args["lulcdata"]
infilt_scope = args["infiltdata"]

sf_config = CFG_DIR / "sfincs_build.yml"

datafolder = Path.cwd() / "data"
datafolder.mkdir(exist_ok=True)


def _set_spatial_ref(ds):
    return ds.set_coords(("spatial_ref"))


## Fetch all the relevant data from datalake

# Get basin data and gdf to define SFINCS region
gdf = get_geodata(basin_scope, bbox=region.total_bounds)
gdf["geometry"].to_file(datafolder / "basins.geojson")

# Get topo tiles and save
outlist = download_tiled_data(dataset=topo_scope, bbox=gdf.total_bounds)
ds_full = xr.open_mfdataset(
    outlist,
)
ds_full.to_netcdf(datafolder / "topo.nc")
del ds_full

# Get gebco data and save
gebco_fn = download_dataset(dataset=bathy_scope)
gebco = xr.open_mfdataset(gebco_fn)
gebco.to_netcdf(datafolder / "bathy.nc")
del gebco

# # Get river data
# rivers = get_geodata(river_scope, bbox=gdf.total_bounds)
# rivers.to_file(datafolder/"rivers.gpkg", driver="GPKG")
# del rivers

# Get merit hydro
outlist = download_tiled_data(dataset=river_scope, bbox=gdf.total_bounds)
ds_full = xr.open_mfdataset(outlist, preprocess=_set_spatial_ref)
ds_full["flwdir"] = ds_full.flwdir.astype(np.uint8)
ds_full.to_netcdf(datafolder / "hydrography.nc")
del ds_full
index_fn = download_single(filename=f"{river_scope}_index.gpkg", rucio_scope="wtromp")

# Get infiltration data
gcn250_fns = download_dataset(dataset=infilt_scope)
gcn250 = xr.open_mfdataset(gcn250_fns)
gcn250.to_netcdf(datafolder / "infiltration.nc")

# Get LULC data
globcover_fn = download_dataset(dataset=lulc_scope)
globcover_ncs = [file for file in globcover_fn if ".nc" in file.name]
globcover = xr.open_mfdataset(globcover_ncs)
# This line is globcover specific, TODO: find way to do this generically
globcover.rename({"GLOBCOVER_L4_200901_200912_V2": "lulc"}).to_netcdf(
    datafolder / "lulc.nc"
)

[globcover_mapping] = [file for file in globcover_fn if "mapping" in file.name]
globcover_mapping.rename(datafolder / "lulc_mapping.csv")

# Clean up rucio downloads
rmtree(Path.cwd() / "wtromp")

## Build SFINCS model

logger = setuplog("sfincs_build", log_level=10)

opt = configread(sf_config)

opt["setup_grid_from_region"].update(res=res)
opt["setup_subgrid"].update(nr_subgrid_pixels=nr_subgrid_pixels)


sf = SfincsModel(root=sf_root, mode="w+", logger=logger)
configwrite(sf_root / "sfincs_build.yml", opt)
sf.build(opt=opt)
