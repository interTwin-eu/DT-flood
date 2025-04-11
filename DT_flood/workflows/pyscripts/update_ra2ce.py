from pathlib import Path
from shutil import copy, copytree, rmtree
import argparse
from pyproj import CRS
import tomllib

from ra2ce.network.network_config_data.network_config_data_reader import (
    NetworkConfigDataReader,
)
from ra2ce.network.network_config_data.network_config_data import HazardSection
from ra2ce.network.network_config_data.enums.aggregate_wl_enum import AggregateWlEnum
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import (
    AnalysisConfigDataReader,
)

import utils_ra2ce_docker

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")
parser.add_argument("--floodmap")

args = parser.parse_args()

# parse arguments
scenario = args.scenario
staticdir = Path(args.static)
hazard_fn = Path(args.floodmap)

print("Copying RA2CE model to output folder")
base_folder = staticdir / "templates" / "ra2ce"
out_folder = staticdir.parent / "output" / "scenarios" / scenario / "Impacts" / "ra2ce"
if out_folder.exists():
    rmtree(out_folder)
copytree(base_folder, out_folder)

print("Setting up hazard")
copy(hazard_fn, out_folder / "static" / "hazard" / hazard_fn.name)

with open(staticdir / "config" / "sfincs.toml", "rb") as f:
    sfincs_config = tomllib.load(f)

crs = CRS.from_string(sfincs_config["config"]["csname"])

network = NetworkConfigDataReader().read(out_folder / "network.ini")
network_hazard = HazardSection(
    hazard_map=[hazard_fn.name],
    hazard_id=None,
    hazard_field_name="waterdepth",
    aggregate_wl=AggregateWlEnum.MAX,
    hazard_crs=crs.to_string(),
)
network.hazard = network_hazard

analysis = AnalysisConfigDataReader().read(out_folder / "analysis.ini")
analysis.analyses[0].threshold = 0.5
analysis.analyses[0].calculate_route_without_disruption = False

# Relative paths are resolved when reading in config data
# Reset them as workdir will change between workflow steps
network.network.polygon = "map.geojson"
network.origins_destinations.origins = "origins.gpkg"
network.origins_destinations.destinations = "destinations.gpkg"

utils_ra2ce_docker.export_NetworkConfigData(network)
utils_ra2ce_docker.export_AnalysisConfigData(analysis)
