from pathlib import Path
from os import makedirs
from shutil import rmtree
import argparse

from DT_flood.utils.fa_scenario_utils import init_scenario, create_scenario

from flood_adapt.object_model.utils import write_finished_file

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")

args = parser.parse_args()

# scenario_fn = Path(args.scenario)
scenario = args.scenario
database_root = Path(args.input).parent

database, scenario = init_scenario(database_root, scenario)

# new_scenario = database.scenarios.get(scenario["name"])
new_scenario = create_scenario(database, scenario)

if new_scenario.results_path.exists():
    print("Removing existing output folder")
    rmtree(new_scenario.results_path)

print(f"Creating output folder at {new_scenario.results_path}")
makedirs(new_scenario.results_path)

write_finished_file(new_scenario.results_path)
