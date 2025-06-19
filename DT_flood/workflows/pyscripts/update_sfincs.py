"""Script for updating sfincs model for FloodAdapt event."""

import argparse
from pathlib import Path

import xarray as xr
from hydromt.log import setuplog
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
database, scenario = init_scenario(database_root, scenario_name)
database = database.database

results_path = database.scenarios.output_path.joinpath(scenario.name)

event = database.events.get(scenario.event)
event_dir = database.input_path / "events" / event.name
projection = database.projections.get(scenario.projection)
strategy = database.strategies.get(scenario.strategy)

sf_adpt = database.static.get_overland_sfincs_model()

sfincs_path = (
    results_path
    / "Flooding"
    / "simulations"
    / database.site.sfincs.config.overland_model.name
)

print(f"Update event {event}")
sf_adpt.set_timing(event.time)

for forcing in event.get_forcings():
    print(f"Setup forcing {forcing}")
    sf_adpt.add_forcing(forcing)

if sf_adpt.rainfall is not None:
    sf_adpt.rainfall *= event.rainfall_multiplier

for measure in strategy.get_hazard_measures():
    print(f"Apply measure {measure}")
    sf_adpt.add_measure(measure)

print(f"Apply projection {projection}")
sf_adpt.add_projection(projection)

filelist = [file.as_posix() for file in event_dir.glob("*.nc")]
if any(["waterlevel" in name for name in filelist]):
    h_fn = event_dir / "waterlevel.nc"
    print(f"Setting up waterlevel from file {h_fn.as_posix()}")
    slr = projection.physical_projection.sea_level_rise.value
    ds_h = xr.open_dataset(h_fn)
    sf_adpt._model.setup_waterlevel_forcing(geodataset=(ds_h + slr))

sf_adpt.write(path_out=sfincs_path)

inp = SfincsInput.from_file(sfincs_path / "sfincs.inp")
config = inp.to_dict()
reftime = config["tref"]

print("Create discharge file")
wf_out = wflow_dir / "model" / "run_default" / "output_scalar.nc"
ds = xr.open_dataset(wf_out)

# Wflow output only starts after first time step so t=0 discharge is missing.
# Correct for by appending zeros

# Assuming constant timestep size in wflow
time_diff = ds["time"][1] - ds["time"][0]
t0 = xr.zeros_like(ds.isel(time=0))
t0["time"] = t0["time"] - time_diff

ds_final = xr.concat([t0, ds], dim="time")
ds_final = ds_final.transpose("time", ...)

df = ds_final["Q_src"].to_pandas()
df.index = (df.index - reftime).total_seconds()
df.to_csv(
    sfincs_path / "sfincs.dis",
    sep=" ",
    header=False,
)
config.update({"disfile": "sfincs.dis", "srcfile": "sfincs.src"})
inp = SfincsInput.from_dict(config)
inp.write(inp_fn=sfincs_path / "sfincs.inp")
