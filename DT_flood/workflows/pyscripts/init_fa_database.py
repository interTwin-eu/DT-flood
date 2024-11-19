from pathlib import Path
from sys import argv
from os import makedirs
from DT_flood.utils.fa_scenario_utils import init_scenario, create_scenario
from flood_adapt.object_model.utils import write_finished_file
from shutil import copytree, rmtree

print("Make extra copies of input folders")
copytree(Path(argv[1])/'input'/"projections", Path(argv[1])/'input'/"Projections", dirs_exist_ok=True)
copytree(Path(argv[1])/"input"/"strategies", Path(argv[1])/"input"/"Strategies", dirs_exist_ok=True)

database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

new_scenario = create_scenario(database, scenario)

new_scenario.init_object_model()

if new_scenario.results_path.exists():
    print("Removing existing output folder")
    rmtree(new_scenario.results_path)

print(f"Creating output folder at {new_scenario.results_path}")
makedirs(new_scenario.results_path)

write_finished_file(new_scenario.results_path)
