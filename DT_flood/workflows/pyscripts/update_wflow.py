from pathlib import Path
from sys import argv
from datetime import datetime
from datetime import timedelta
import tomli

from hydromt.log import setuplog
from hydromt_wflow import WflowModel

from flood_adapt.object_model.scenario import Scenario

fa_database_fn = Path(argv[1])
scenario_fn = fa_database_fn / (argv[2]+"_toplevel.toml")
mode = argv[3]
                       
print(f"Configuring WFlow event run for FloodAdapt Database {fa_database_fn.stem} with scenario {argv[2]}")

with open(scenario_fn, 'rb') as f:
    scenario = tomli.load(f)

wflow_root = fa_database_fn / 'static' / 'templates' / 'wflow'
logger = setuplog("update_wflow", log_level=10)

wf = WflowModel(
    root=wflow_root,
    data_libs=scenario['event']['data_catalogues'],
    mode='r',
    logger=logger,
)
wf.read()

if mode=="warmup":
    print("Updating WFlow model for warmup run")
    endtime = datetime.strptime(scenario['event']['start_time'], "%Y-%m-%d %H:%M:%S")
    starttime = endtime - timedelta(days=365)
    precip_fn = scenario['event']['wflow_forcing']['precip_warmup']
    pet_fn = scenario['event']['wflow_forcing']['pet_warmup']
    opt = {
        "setup_config": {
            "starttime": datetime.strftime(starttime, "%Y-%m-%dT%H:%M:%S"),
            "endtime": datetime.strftime(endtime, "%Y-%m-%dT%H:%M:%S"),
            "timestepsecs": 86400,
            "model.reinit": True,
            "state.path_output": "../../wflow_event/instate/instates.nc",
            "input.path_static": "./staticmaps.nc",
        },
    }
elif mode == "event":
    print("Updating WFlow model for event run")
    starttime = datetime.strptime(scenario['event']['start_time'], "%Y-%m-%d %H:%M:%S")
    endtime = datetime.strptime(scenario['event']['end_time'], "%Y-%m-%d %H:%M:%S")
    precip_fn = scenario['event']['wflow_forcing']['precip_event']
    pet_fn = scenario['event']['wflow_forcing']['pet_event']
    opt = {
        "setup_config": {
            "starttime": datetime.strftime(starttime, "%Y-%m-%dT%H:%M:%S"),
            "endtime": datetime.strftime(endtime, "%Y-%m-%dT%H:%M:%S"),
            "timestepsecs": 3600,
            "model.reinit": False,
            "input.path_static": "./staticmaps.nc",
        },
    }
else:
    raise RuntimeError("Select a valid mode for WFlow run")


forcing_config = {    
    "setup_precip_forcing": {
        "precip_fn": precip_fn,
        "precip_clim_fn": None,
    },
    "setup_temp_pet_forcing": {
        "temp_pet_fn": pet_fn,
        "press_correction": True,
        "temp_correction": True,
        "pet_method": "debruin",
        "skip_pet": False,
        "dem_forcing_fn": scenario['event']['wflow_forcing']['orography'],
    }
}
opt.update(forcing_config)

wf_new_root = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / ("wflow_"+mode)
wf.set_root(wf_new_root, mode="w+")
wf.update(wf_new_root, opt=opt, write=False)
wf.write()