"""Script for postprocessing SFINCS run."""

import argparse
from pathlib import Path

import hydromt_sfincs.utils as utils
import xarray as xr
from hydromt.log import setuplog
from hydromt_sfincs import SfincsModel

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")
parser.add_argument("--sfincsdir")

args = parser.parse_args()

logger = setuplog("update_sfincs", log_level=10)

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent
sf_root = Path(args.sfincsdir) / "data"

# Fetch FA database, misc
database, scenario = init_scenario(database_root, scenario_name)
database = database.database
demfile = database.static_path / "dem" / database.site.sfincs.dem.filename
floodmap_fn = f"FloodMap_{scenario_name}.tif"
zsmax_fn = "max_water_level_map.nc"

sf = SfincsModel(root=sf_root, logger=logger, mode="r+")
sf.read()

zsmax = sf.results["zsmax"].max(dim="timemax")
dem = sf.data_catalog.get_rasterdataset(demfile)

utils.downscale_floodmap(zsmax=zsmax, dep=dem, hmin=0.01, floodmap_fn=floodmap_fn)

hazard = xr.open_dataarray(floodmap_fn)
hazard = hazard.rio.reproject(hazard.rio.crs)
hazard.rio.to_raster(floodmap_fn)

zsmax.to_netcdf(zsmax_fn)
