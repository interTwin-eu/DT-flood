from pathlib import Path
from sys import argv
from flood_adapt.object_model.scenario import Scenario


def tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")

tree(Path(argv[1]))

scenario_fn = Path(argv[1]) / "input" / "scenarios" / argv[2] / (argv[2]+".toml")
scenario = Scenario.load_file(scenario_fn)

scenario.init_object_model()
# print(f"Scenario database path: {scenario.database_input_path}")

print("Downscaling and writing floodmap")
scenario.direct_impacts.hazard.write_floodmap_geotiff()
scenario.direct_impacts.hazard._set_sfincs_map_path(mode='single_event')
print(f"Floodmap written to {scenario.direct_impacts.hazard.sfincs_map_path}")

print("Preparing FIAT configuration")
scenario.direct_impacts.preprocess_fiat()



# print(f"Scenario Hazard sim path: {scenario.direct_impacts.hazard.simulation_paths}")
# print(f"SFINCS has run succesfully: {scenario.direct_impacts.hazard.has_run}")
# print(f"SFINCS checker: {scenario.direct_impacts.hazard.sfincs_has_run_check()}")
# print(f"SFINCS has run succesfully double check: {scenario.direct_impacts.hazard.has_run}")