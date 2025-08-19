"""Script for updating RA2CE model. Run inside container."""

import argparse
import configparser
import tomllib
from pathlib import Path
from shutil import copy, copytree, rmtree

from pyproj import CRS

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

network_config = configparser.ConfigParser()
network_config.read(out_folder / "network.ini")

network_config["hazard"]["hazard_map"] = hazard_fn.name
network_config["hazard"]["hazard_field_name"] = "waterdepth"
network_config["hazard"]["aggregate_wl"] = "max"
network_config["hazard"]["hazard_crs"] = crs.to_string()

network_config["network"]["polygon"] = "map.geojson"
network_config["origins_destinations"]["origins"] = "origins.gpkg"
network_config["origins_destinations"]["destinations"] = "destinations.gpkg"

with open(out_folder / "network.ini", mode="w", encoding="utf-8") as f:
    network_config.write(f)


analysis_config = configparser.ConfigParser()
analysis_config.read(out_folder / "analysis.ini")

analysis_config["analysis1"]["threshold"] = "0.5"
analysis_config["analysis1"]["calculate_route_without_disruption"] = "True"

analysis_config["origins_destinations"]["origins"] = "origins.gpkg"
analysis_config["origins_destinations"]["destinations"] = "destinations.gpkg"
analysis_config["origins_destinations"]["origins_names"] = "A"
analysis_config["origins_destinations"]["destinations_names"] = "B"
analysis_config["origins_destinations"]["id_nmae_origin_destination"] = "OBJECT ID"
analysis_config["origins_destinations"]["origin_count"] = "POPULATION"
analysis_config["origins_destinations"]["category"] = "category"

with open(out_folder / "analysis.ini", mode="w", encoding="utf-8") as f:
    analysis_config.write(f)


# network = NetworkConfigDataReader().read(out_folder / "network.ini")
# network_hazard = HazardSection(
#     hazard_map=[hazard_fn.name],
#     hazard_id=None,
#     hazard_field_name="waterdepth",
#     aggregate_wl=AggregateWlEnum.MAX,
#     hazard_crs=crs.to_string(),
# )
# network.hazard = network_hazard

# analysis = AnalysisConfigDataReader().read(out_folder / "analysis.ini")
# analysis.analyses[0].threshold = 0.5
# analysis.analyses[0].calculate_route_without_disruption = True

# analysis.origins_destinations.origins = "origins.gpkg"
# analysis.origins_destinations.destinations = "destinations.gpkg"
# analysis.origins_destinations.origins_names = "A"
# analysis.origins_destinations.destinations_names = "B"
# analysis.origins_destinations.id_name_origin_destinatiom = "OBJECT ID"
# analysis.origins_destinations.origin_count = "POPULATION"
# analysis.origins_destinations.category = "category"


# # Relative paths are resolved when reading in config data
# # Reset them as workdir will change between workflow steps
# network.network.polygon = "map.geojson"
# network.origins_destinations.origins = "origins.gpkg"
# network.origins_destinations.destinations = "destinations.gpkg"

# utils_ra2ce_docker.export_NetworkConfigData(network)
# utils_ra2ce_docker.export_AnalysisConfigData(analysis)
