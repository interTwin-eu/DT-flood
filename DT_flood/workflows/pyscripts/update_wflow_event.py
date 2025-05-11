"""Script to update the Wflow model with a new event."""

import argparse
from datetime import datetime
from pathlib import Path
from shutil import copy

from hydromt.log import setuplog
from hydromt_wflow import WflowModel

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")
parser.add_argument("--warmup_dir")

args = parser.parse_args()

logger = setuplog("update_wflow", log_level=10)

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent
warmup_dir = Path(args.warmup_dir) / "model"
warmup_states = warmup_dir / "run_default" / "outstate" / "outstates.nc"

# unpack FA database, scenario, event description
database, scenario_config = init_scenario(database_root, scenario_name)
database = database.database
scenario = database.scenarios.get(scenario_config["name"])

results_path = database.scenarios.output_path.joinpath(scenario.name)


event = scenario_config["event"]
event_dir = database.input_path / "events" / scenario.event


wflow_root = database.static_path / "templates" / "wflow"
wf = WflowModel(
    root=wflow_root,
    data_libs=[],
    mode="r",
    logger=logger,
)
wf.read()

starttime = datetime.strptime(
    scenario_config["event"]["start_time"], "%Y-%m-%d %H:%M:%S"
)
endtime = datetime.strptime(scenario_config["event"]["end_time"], "%Y-%m-%d %H:%M:%S")

opt = {
    "setup_config": {
        "starttime": datetime.strftime(starttime, "%Y-%m-%dT%H:%M:%S"),
        "endtime": datetime.strftime(endtime, "%Y-%m-%dT%H:%M:%S"),
        "timestepsecs": 3600,
        "model.reinit": False,
        "input.path_static": "./staticmaps.nc",
    },
}

forcing_config = {
    "setup_precip_forcing": {
        "precip_fn": (event_dir / "precip_event.nc").as_posix(),
        "precip_clim_fn": None,
    },
    "setup_temp_pet_forcing": {
        "temp_pet_fn": (event_dir / "pet_event.nc").as_posix(),
        "press_correction": True,
        "temp_correction": True,
        "pet_method": "debruin",
        "skip_pet": False,
        "dem_forcing_fn": (event_dir / "orography.nc").as_posix(),
    },
}
opt.update(forcing_config)

wf_event_root = results_path / "Flooding" / "simulations" / "wflow_event"
wf.set_root(wf_event_root, mode="w+")
wf.update(wf_event_root, opt=opt, write=False)
wf.write()

instates = wf_event_root / "instate" / "instates.nc"
copy(warmup_states, instates)
