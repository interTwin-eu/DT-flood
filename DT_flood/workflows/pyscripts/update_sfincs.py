from pathlib import Path
from datetime import datetime
import xarray as xr
import argparse

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
scenario = database.scenarios.get(scenario_config["name"])
event = scenario_config["event"]

start_time = datetime.strptime(scenario_config['event']['start_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario_config['event']['end_time'],"%Y-%m-%d %H:%M:%S")

sf_adpt = database.static.get_overland_sfincs_model()
sf_adpt.preprocess(scenario)

sfincs_path = scenario.results_path / "Flooding" / "simulations" / database.site.attrs.sfincs.config.overland_model
sf = SfincsModel(
    root=sfincs_path,
    mode="r",
    data_libs=event["data_catalogues"],
    logger=logger
)
sf.read()

if "waterlevel" in event["sfincs_forcing"]:
    h_fn = database.input_path / "events" / event["name"] / "waterlevel.nc"
    slr = scenario.projection.get_physical_projection().attrs.sea_level_rise.value
    ds_h = xr.open_dataset(h_fn)
    sf.setup_waterlevel_forcing(geodataset=(ds_h['waterlevel']+slr))

inp = SfincsInput.from_file(sfincs_path/"sfincs.inp")
config = inp.to_dict()
reftime = config["tref"]


wf_out = wflow_dir / "model" / "run_default" / "output_scalar.nc"
ds = xr.open_dataset(wf_out)
df = ds["Q_src"].to_pandas()
df.index = (df.index - reftime).total_seconds()
df.to_csv(
    sfincs_path/"sfincs.dis",
    sep = " ",
    header=False,
)
config.update({"disfile": "sfincs.dis", "srcfile": "sfincs.src"})
inp = SfincsInput.from_dict(config)
inp.write(inp_fn=sfincs_path/"sfincs.inp")

