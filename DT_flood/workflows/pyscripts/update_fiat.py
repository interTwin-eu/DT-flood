"""Script for updating FIAT model."""

import argparse
from pathlib import Path

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--output")
parser.add_argument("--scenario")
parser.add_argument("--floodmap")
parser.add_argument("--waterlevelmap")

args = parser.parse_args()

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent
floodmap_fn = Path(args.floodmap)
waterlevel_fn = Path(args.waterlevelmap)

# Fetch FA database, misc
database, scenario_config = init_scenario(database_root, scenario_name)
database = database.database
scenario = database.scenarios.get(scenario_config["name"])
map_type = database.site.fiat.config.floodmap_type

print("Fetching FIAT model")
fa_adpt = database.static.get_fiat_model()

print("Setting up FIAT projection")
fa_adpt.add_projection(database.projections.get(scenario.projection))
strategy = database.strategies.get(scenario.strategy)
print("Adding FIAT measures")
for measure in strategy.get_measures():
    fa_adpt.add_measure(measure)

print("Setting up FIAT hazard")
if map_type == "water_level":
    map_fn = waterlevel_fn
    var = "zsmax"
elif map_type == "water_depth":
    map_fn = floodmap_fn
    var = None
else:
    raise ValueError("No Valid Floodmap Type")

print(f"Floodmap: {map_fn}")
print(f"Floodmap type: {var}")
fa_adpt._model.setup_hazard(map_fn=map_fn, map_type=map_type, var=var, nodata=-999)

fiat_path = database.output_path.joinpath(
    "scenarios", scenario.name, "Impacts", "fiat_model"
)
print(f"Saving FIAT model to {fiat_path}")
fa_adpt.write(path_out=fiat_path)
