import os
from pathlib import Path
from sys import argv
import xarray as xr

from DT_flood.utils.fa_scenario_utils import init_scenario


database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario_obj = database.scenarios.get(scenario['name'])

scenario_obj.init_object_model()


scenario_obj.direct_impacts.hazard.set_simulation_paths()
print("Writing water levels map")
scenario_obj.direct_impacts.hazard.write_water_level_map()
print("Writing downscaled floodmap")
scenario_obj.direct_impacts.hazard.write_floodmap_geotiff()
scenario_obj.direct_impacts.hazard.set_event()
scenario_obj.direct_impacts.hazard._get_flood_map_path()
print(f"Floodmap written to {scenario_obj.direct_impacts.hazard.flood_map_path}")
hazard_fn = scenario_obj.results_path/"Flooding"/f"FloodMap_{scenario['name']}.tif"
hazard = xr.open_dataarray(hazard_fn)
hazard = hazard.rio.reproject(hazard.rio.crs)
hazard.rio.to_raster(str(hazard_fn))
