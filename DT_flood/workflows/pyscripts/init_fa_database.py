from pathlib import Path
from sys import argv
from os import makedirs
from DT_flood.utils.fa_scenario_utils import init_scenario, create_scenario

# scenario_fn = Path(argv[1]) /(argv[2]+"_toplevel.toml")

database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

new_scenario = create_scenario(database, scenario)

new_scenario.init_object_model()

if not scenario.results_path.exists():
    print(f"Creating output folder at {scenario.results_path}")
    makedirs(scenario.results_path)
else:
    print(f"Output folder already exists at {scenario.results_path}")

# print("Preparing SFINCS configuration")
# scenario.direct_impacts.hazard.preprocess_sfincs()