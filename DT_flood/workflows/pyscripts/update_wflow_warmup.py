from pathlib import Path
from datetime import datetime
from datetime import timedelta
import argparse

from hydromt.log import setuplog
from hydromt_wflow import WflowModel

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")

args = parser.parse_args()

logger = setuplog("update_wflow", log_level=10)

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent

# unpack FA database, scenario, event description
database, scenario_config = init_scenario(database_root, scenario_name)
scenario = database.scenarios.get(scenario_config["name"])
event = scenario_config["event"]

# wflow template model
wflow_root = database.static_path / "templates" / "wflow"
wf = WflowModel(
    root=wflow_root,
    data_libs=scenario_config['event']['data_catalogues'],
    mode='r',
    logger=logger,
)
wf.read()

print("Updating WFlow model for warmup run")
endtime = datetime.strptime(event['start_time'], "%Y-%m-%d %H:%M:%S")
starttime = endtime - timedelta(days=365)
precip_fn = event['wflow_forcing']['precip_warmup']
pet_fn = event['wflow_forcing']['pet_warmup']
opt = {
    "setup_config": {
        "starttime": datetime.strftime(starttime, "%Y-%m-%dT%H:%M:%S"),
        "endtime": datetime.strftime(endtime, "%Y-%m-%dT%H:%M:%S"),
        "timestepsecs": 86400,
        "model.reinit": True,
        "input.path_static": "./staticmaps.nc",
    },
}

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
        "dem_forcing_fn": event['wflow_forcing']['orography'],
    }
}
opt.update(forcing_config)

wf_warmup_root = scenario.results_path / "Flooding" / "simulations" / "wflow_warmup"
wf.set_root(wf_warmup_root, mode="w+")
wf.update(wf_warmup_root, opt=opt, write=False)
wf.write()