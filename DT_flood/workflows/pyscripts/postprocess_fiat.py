"""Script for postprocessing FIAT run."""

import argparse
from pathlib import Path
from shutil import copytree

from flood_adapt.adapter.fiat_adapter import FiatAdapter

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")
parser.add_argument("--fiatdir")

args = parser.parse_args()

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent
fiatdir = Path(args.fiatdir)

# Fetch FA database, misc
database, scenario_config = init_scenario(database_root, scenario_name)
database = database.database

scenario = database.scenarios.get(scenario_config["name"])

fiat_out_root = database.output_path.joinpath(
    "scenarios", scenario.name, "Impacts", "fiat_model"
)
print(f"Copying FIAT model from {fiatdir} to {fiat_out_root}")
copytree(fiatdir, fiat_out_root)

fiat_adpt = FiatAdapter(
    model_root=fiat_out_root,
    config=database.site.fiat.config,
    config_base_path=database.static_path,
)
print(f"Adapter model root: {fiat_adpt._model.root}")
print(f"Adapter config path: {fiat_adpt.config_base_path}")

fiat_adpt.read_outputs()
fiat_adpt.postprocess(scenario=scenario)
