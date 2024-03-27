from pathlib import Path
from sys import argv
from datetime import datetime
from datetime import timedelta

from hydromt.log import setuplog
from hydromt_wflow import WflowModel

from flood_adapt.object_model.scenario import Scenario

fa_database_fn = Path(argv[1])
scenario_fn = fa_database_fn / "input" / "scenarios" / argv[2] / (argv[2]+".toml")
data_catalog_fn = Path(argv[3])

print(f"Configuring WFlow event run for FloodAdapt Database {fa_database_fn.stem} with scenario {argv[2]}")

scenario = Scenario.load_file(scenario_fn)
scenario.init_object_model()

starttime = datetime.strptime(scenario.direct_impacts.hazard.event.attrs.time.start_time, "%Y%m%d %H%M%S")
endtime = datetime.strptime(scenario.direct_impacts.hazard.event.attrs.time.end_time, "%Y%m%d %H%M%S")

wflow_root = fa_database_fn / 'static' / 'templates' / 'wflow'
logger = setuplog("update_wflow", log_level=10)

wf = WflowModel(
    root=wflow_root,
    data_libs=data_catalog_fn,
    mode='r',
    logger=logger,
)
wf.read()

opt = {
    "setup_config": {
        "starttime": datetime.strftime(starttime, "%Y-%m-%dT%H:%M:%S"),
        "endtime": datetime.strftime(endtime, "%Y-%m-%dT%H:%M:%S"),
        "model.reinit": False,
        "input.path_static": "./staticmaps.nc",
    },
    "setup_precip_forcing": {
        "precip_fn": "era5_hourly",
        "precip_clim_fn": None,
    },
    "setup_temp_pet_forcing": {
        "temp_pet_fn": "era5_hourly",
        "press_correction": True,
        "temp_correction": True,
        "pet_method": "debruin",
        "skip_pet": False,
    }
}

wf_event_root = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / "wflow"
wf.set_root(wf_event_root, mode="w+")
wf.update(wf_event_root, opt=opt, write=False)
wf.write()