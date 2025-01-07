from pathlib import Path
from sys import argv
from datetime import datetime
from datetime import timedelta
import tomli

from hydromt.log import setuplog
from hydromt_wflow import WflowModel
from DT_flood.utils.fa_scenario_utils import init_scenario

def tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")

# fa_database_fn = Path(argv[1])
# scenario_fn = fa_database_fn / (argv[2]+"_toplevel.toml")
mode = argv[3]

database, scenario_config = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))
scenario = database.scenarios.get(scenario_config["name"])

print(f"Configuring WFlow event run for FloodAdapt Database {Path(argv[1]).stem} with scenario {argv[2]}")

# with open(scenario_fn, 'rb') as f:
#     scenario_config = tomli.load(f)
#
# wflow_root = fa_database_fn / 'static' / 'templates' / 'wflow'
wflow_root = database.static_path / "templates" / "wflow"
logger = setuplog("update_wflow", log_level=10)

wf = WflowModel(
    root=wflow_root,
    data_libs=scenario_config['event']['data_catalogues'],
    mode='r',
    logger=logger,
)
wf.read()

if mode=="warmup":
    print("Updating WFlow model for warmup run")
    endtime = datetime.strptime(scenario_config['event']['start_time'], "%Y-%m-%d %H:%M:%S")
    starttime = endtime - timedelta(days=365)
    precip_fn = scenario_config['event']['wflow_forcing']['precip_warmup']
    pet_fn = scenario_config['event']['wflow_forcing']['pet_warmup']
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
    starttime = datetime.strptime(scenario_config['event']['start_time'], "%Y-%m-%d %H:%M:%S")
    endtime = datetime.strptime(scenario_config['event']['end_time'], "%Y-%m-%d %H:%M:%S")
    precip_fn = scenario_config['event']['wflow_forcing']['precip_event']
    pet_fn = scenario_config['event']['wflow_forcing']['pet_event']
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
        "dem_forcing_fn": scenario_config['event']['wflow_forcing']['orography'],
    }
}
opt.update(forcing_config)
#
# wf_new_root = fa_database_fn / "output" / "scenarios" / argv[2] / "Flooding" / "simulations" / ("wflow_"+mode)
wf_new_root = scenario.results_path / "Flooding" / "simulations" / ("wflow_"+mode)
wf.set_root(wf_new_root, mode="w+")
wf.update(wf_new_root, opt=opt, write=False)
wf.write()

tree(Path(argv[1]))

database.shutdown()

# tree(fa_database_fn)