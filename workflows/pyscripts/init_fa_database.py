from pathlib import Path
from sys import argv
from os import makedirs
from flood_adapt.object_model.scenario import Scenario

scenario_fn = Path(argv[1]) / "input" / "scenarios" / argv[2] / (argv[2]+".toml")
scenario = Scenario.load_file(scenario_fn)

scenario.init_object_model()

if not scenario.results_path.exists():
    print(f"Creating output folder at {scenario.results_path}")
    makedirs(scenario.results_path)
else:
    print(f"Output folder already exists at {scenario.results_path}")

print("Preparing SFINCS configuration")
scenario.direct_impacts.hazard.preprocess_sfincs()