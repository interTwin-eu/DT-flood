from pathlib import Path
import argparse

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
scenario = database.scenarios.get(scenario_config["name"])
map_type = database.site.attrs.fiat.config.floodmap_type

fa_adpt = database.static.get_fiat_model()

fa_adpt.add_projection(scenario.projection)
for measure in scenario.strategy.get_impact_strategy().measures:
    fa_adpt.add_measure(measure)

if map_type == "water_level":
    map_fn = waterlevel_fn
    var = "zsmax"
elif map_type == "water_depth":
    map_fn = floodmap_fn
    var = None
else:
    raise ValueError("No Valid Floodmap Type")

fa_adpt._model.setup_hazard(map_fn=map_fn, map_type=map_type, var=var, nodata=-999)

fiat_path = scenario.impacts.impacts_path / "fiat_model"
fa_adpt.write(path_out=fiat_path)
