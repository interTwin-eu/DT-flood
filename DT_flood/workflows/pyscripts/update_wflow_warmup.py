"""Script to update the Wflow model for warmup run."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

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
database = database.database
scenario = database.scenarios.get(scenario_config["name"])

results_path = database.scenarios.output_path.joinpath(scenario.name)


event = scenario_config["event"]
event_dir = database.input_path / "events" / scenario.event

# wflow template model
wflow_root = database.static_path / "templates" / "wflow"
wf = WflowModel(
    root=wflow_root,
    data_libs=[],
    mode="r",
    logger=logger,
)
wf.read()

print("Updating WFlow model for warmup run")
endtime = datetime.strptime(event["start_time"], "%Y-%m-%d %H:%M:%S")
starttime = endtime - timedelta(days=365)

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
        "precip_fn": (event_dir / "precip_warmup.nc").as_posix(),
        "precip_clim_fn": None,
    },
    "setup_temp_pet_forcing": {
        "temp_pet_fn": (event_dir / "pet_warmup.nc").as_posix(),
        "press_correction": True,
        "temp_correction": True,
        "pet_method": "debruin",
        "skip_pet": False,
        "dem_forcing_fn": (event_dir / "orography.nc").as_posix(),
    },
}
opt.update(forcing_config)

wf_warmup_root = results_path / "Flooding" / "simulations" / "wflow_warmup"
wf.set_root(wf_warmup_root, mode="w+")
wf.update(wf_warmup_root, opt=opt, write=False)
wf.write()
