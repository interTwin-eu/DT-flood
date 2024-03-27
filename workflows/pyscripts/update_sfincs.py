from pathlib import Path
from sys import argv

from hydromt.log import setuplog
from hydromt_wflow import WflowModel
from hydromt_sfincs.sfincs_input import SfincsInput

from flood_adapt.object_model.scenario import Scenario

fa_database_fn = Path(argv[1])
# scenario_fn = fa_database_fn / "input" / "scenarios" / argv[2] / (argv[2]+".toml")

wflow_path = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / "wflow_event"
sfincs_path = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / "overland"

print(f"Updating SFINCS model for Scenario {argv[2]} with discharge from WFLOW model at {str(wflow_path)}")

logger = setuplog("Update overland SFINCS", log_level=10)
wf = WflowModel(
    root=wflow_path,
    mode="r",
    logger=logger
)
wf.read()

inp = SfincsInput.from_file(sfincs_path/"sfincs.inp")
config = inp.to_dict()

reftime = config["tref"]
df = wf.results['netcdf']["Q_src"].to_pandas()
df.index = (df.index - reftime).total_seconds()
df.to_csv(
    sfincs_path/"sfincs.dis",
    sep = " ",
    header=False,
)

config.update({"disfile": "sfincs.dis"})
inp = SfincsInput.from_dict(config)
inp.write(inp_fn=sfincs_path/"sfincs.inp")


