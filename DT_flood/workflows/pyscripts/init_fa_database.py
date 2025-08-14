"""Script for initializing FloodAdapt scenario."""

import argparse
from os import makedirs
from pathlib import Path
from shutil import rmtree

from flood_adapt.misc.utils import write_finished_file

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")

args = parser.parse_args()

scenario = args.scenario
database_root = Path(args.input).parent

database, scenario = init_scenario(database_root, scenario)

results_path = database.database.scenarios.output_path.joinpath(scenario.name)

if results_path.exists():
    print("Removing existing output folder")
    rmtree(results_path)

print(f"Creating output folder at {results_path}")
makedirs(results_path)

write_finished_file(results_path)
