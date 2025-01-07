from pathlib import Path
from shutil import copy, copytree, rmtree
from sys import argv
import tomli
import xarray as xr
from pyproj import CRS

from ra2ce.network.network_config_data.network_config_data_reader import NetworkConfigDataReader
from ra2ce.network.network_config_data.network_config_data import HazardSection
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import AnalysisConfigDataReader

import utils_ra2ce_docker
# parse arguments
fa_database_fn = Path(argv[1])
scenario_fn = fa_database_fn / (argv[2]+"_toplevel.toml")

with open(fa_database_fn/"static"/"site"/"site.toml",'rb') as f:
    site = tomli.load(f)

print(f"Copying RA2CE model to output folder")
base_folder = fa_database_fn/"static"/"templates"/"ra2ce"
out_folder = fa_database_fn/"output"/"scenarios"/argv[2]/"Impacts"/"ra2ce"
if out_folder.exists():
    rmtree(out_folder)
copytree(base_folder,out_folder)

print(f"Setting up hazard")
hazard_fn = fa_database_fn/"output"/"scenarios"/argv[2]/"Flooding"/f"FloodMap_{argv[2]}.tif"
copy(hazard_fn,out_folder/"static"/"hazard"/hazard_fn.name)
# Make sure CRS and Affine transform of hazard map is correct
# TODO: Move to sfincs postprocess
# hazard = xr.open_dataarray(out_folder/"static"/"hazard"/hazard_fn.name)
# hazard = hazard.rio.reproject(hazard.rio.crs)
# hazard.rio.to_raster(str(out_folder/"static"/"hazard"/hazard_fn.name))

crs = CRS.from_string(site['sfincs']['csname'])

network = NetworkConfigDataReader().read(out_folder/"network.ini")
network_hazard = HazardSection(
    hazard_map = [hazard_fn.name],
    hazard_id = None,
    hazard_field_name = "waterdepth",
    aggregate_wl = AggregateWlEnum.MAX,
    hazard_crs = crs.to_string(),
)
network.hazard = network_hazard

analysis = AnalysisConfigDataReader().read(out_folder/"analysis.ini")
analysis.analyses[0].aggregate_wl = "max"
analysis.analyses[0].threshold = 0.5
analysis.analyses[0].calculate_route_without_disruption = False

# Relative paths are resolved when reading in config data
# Reset them as workdir will change between workflow steps
network.network.polygon = "map.geojson"
network.origins_destinations.origins = "origins.gpkg"
network.origins_destinations.destinations = "destinations.gpkg"

utils_ra2ce_docker.export_NetworkConfigData(network)
utils_ra2ce_docker.export_AnalysisConfigData(analysis)