import os
from pathlib import Path
from sys import argv

from flood_adapt.api import scenarios
from DT_flood.utils.fa_scenario_utils import init_scenario

from flood_adapt.object_model.interface.events import Mode


database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario_obj = scenarios.get_scenario(scenario['name'])

scenario_obj.init_object_model()

print("Downscaling and writing floodmap")
scenario_obj.direct_impacts.hazard.set_simulation_paths()
scenario_obj.direct_impacts.hazard.write_water_level_map()
scenario_obj.direct_impacts.hazard.write_floodmap_geotiff()
scenario_obj.direct_impacts.hazard.set_event()
scenario_obj.direct_impacts.hazard.has_run = scenario_obj.direct_impacts.hazard.has_run_check()
print(f"Floodmap written to {scenario_obj.direct_impacts.hazard.flood_map_path}")
print(f"Event mode: {scenario_obj.direct_impacts.hazard.event_mode}")
print(f"Check if risk: {scenario_obj.direct_impacts.hazard.event_mode == Mode.risk}")

# def tree(directory):
#     print(f"+ {directory}")
#     for path in sorted(directory.rglob('*')):
#         depth = len(path.relative_to(directory).parts)
#         spacer = "  " * depth
#         print(f"{spacer}+ {path.name}")

# tree(Path(argv[1]))

print("Preparing FIAT configuration")
scenario_obj.direct_impacts.preprocess_fiat()

risk_out = scenario_obj.direct_impacts.fiat_path/"hazard"/"risk_map.nc"

if not scenario_obj.direct_impacts.hazard.event_mode == Mode.risk and risk_out.exists():
    risk_out.rename(scenario_obj.direct_impacts.fiat_path/"hazard"/"hazard_map.nc")
