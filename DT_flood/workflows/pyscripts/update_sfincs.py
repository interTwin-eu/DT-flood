"""Script for updating sfincs model for FloodAdapt event."""

import argparse
from datetime import datetime
from pathlib import Path

import xarray as xr
from hydromt.log import setuplog
from hydromt_sfincs import SfincsModel
from hydromt_sfincs.sfincs_input import SfincsInput

from DT_flood.utils.fa_scenario_utils import init_scenario

parser = argparse.ArgumentParser()
parser.add_argument("--input")
parser.add_argument("--static")
parser.add_argument("--scenario")
parser.add_argument("--wflowdir")

args = parser.parse_args()

logger = setuplog("update_sfincs", log_level=10)

# Unpack args
scenario_name = args.scenario
database_root = Path(args.input).parent
wflow_dir = Path(args.wflowdir)

# unpack FA database, scenario, event description
database, scenario_config = init_scenario(database_root, scenario_name)
database = database.database
scenario = database.scenarios.get(scenario_config["name"])

results_path = database.scenarios.output_path.joinpath(scenario.name)

event_dict = scenario_config["event"]
event = database.events.get(scenario.event)
projection = database.projections.get(scenario.projection)
strategy = database.strategies.get(scenario.strategy)

start_time = datetime.strptime(
    scenario_config["event"]["start_time"], "%Y-%m-%d %H:%M:%S"
)
end_time = datetime.strptime(scenario_config["event"]["end_time"], "%Y-%m-%d %H:%M:%S")

sf_adpt = database.static.get_overland_sfincs_model()

sfincs_path = (
    results_path
    / "Flooding"
    / "simulations"
    / database.site.sfincs.config.overland_model.name
)

sf_adpt.set_timing(event.time)
for forcing in event.get_forcings():
    sf_adpt.add_forcing(forcing)

if sf_adpt.rainfall is not None:
    sf_adpt.rainfall *= event.rainfall_multiplier

for measure in strategy.get_hazard_measures():
    sf_adpt.add_measure(measure)

sf_adpt.add_projection(projection)

sf_adpt.write(path_out=sfincs_path)

sf = SfincsModel(root=sfincs_path, mode="r", logger=logger)
sf.read()

if "waterlevel" in event_dict["sfincs_forcing"]:
    h_fn = database.input_path / "events" / event_dict["name"] / "waterlevel.nc"
    slr = projection.physical_projection.sea_level_rise.value
    ds_h = xr.open_dataset(h_fn)
    sf.setup_waterlevel_forcing(geodataset=(ds_h + slr))

inp = SfincsInput.from_file(sfincs_path / "sfincs.inp")
config = inp.to_dict()
reftime = config["tref"]


wf_out = wflow_dir / "model" / "run_default" / "output_scalar.nc"
ds = xr.open_dataset(wf_out)
df = ds["Q_src"].to_pandas()
df.index = (df.index - reftime).total_seconds()
df.to_csv(
    sfincs_path / "sfincs.dis",
    sep=" ",
    header=False,
)
config.update({"disfile": "sfincs.dis", "srcfile": "sfincs.src"})
inp = SfincsInput.from_dict(config)
inp.write(inp_fn=sfincs_path / "sfincs.inp")
