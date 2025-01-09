import os
from pathlib import Path
from sys import argv
import glob

from flood_adapt.api import scenarios
from flood_adapt.object_model.interface.events import Mode
from DT_flood.utils.fa_scenario_utils import init_scenario

from flood_adapt.object_model.interface.events import Mode


database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario_obj = scenarios.get_scenario(scenario['name'])

scenario_obj.init_object_model()

scenario_obj.direct_impacts.hazard.set_simulation_paths()
scenario_obj.direct_impacts.hazard.write_water_level_map()
scenario_obj.direct_impacts.hazard.write_floodmap_geotiff()
scenario_obj.direct_impacts.hazard._get_flood_map_path()
scenario_obj.direct_impacts.hazard.set_event()
print(f"Floodmap written to {scenario_obj.direct_impacts.hazard.flood_map_path}")
print(f"Event mode: {scenario_obj.direct_impacts.hazard.event_mode}")
print(f"Check if risk: {scenario_obj.direct_impacts.hazard.event_mode == Mode.risk}")


print("Preparing FIAT configuration")
scenario_obj.direct_impacts.preprocess_fiat()

fiat_path = scenario_obj.results_path/"Impacts"/"fiat_model"
hazard_fn, = glob.glob(str(fiat_path/'hazard')+"/*.nc")

print("Fix hazard map naming")
if "risk" in Path(hazard_fn).name and scenario_obj.direct_impacts.hazard.event_mode == Mode.single_event:
    Path(hazard_fn).replace(Path(hazard_fn).parent/"hazard_map.nc")

