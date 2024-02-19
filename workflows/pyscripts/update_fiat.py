from pathlib import Path
from sys import argv
from flood_adapt.object_model.scenario import Scenario

scenario_fn = Path(argv[1]) / "input" / "scenarios" / argv[2] / (argv[2]+".toml")
scenario = Scenario.load_file(scenario_fn)

scenario.init_object_model()

print("Preparing FIAT configuration")
scenario.direct_impacts.preprocess_fiat()