from pathlib import Path
from sys import argv
from datetime import datetime

from hydromt.log import setuplog
from hydromt_wflow import WflowModel
from hydromt_sfincs import SfincsModel
from hydromt_sfincs.sfincs_input import SfincsInput
from DT_flood.utils.fa_scenario_utils import init_scenario
# from flood_adapt.object_model.scenario import Scenario

database, scenario = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))

# scenario_fn = fa_database_fn / "input" / "scenarios" / argv[2] / (argv[2]+".toml")

wflow_path = database.output_path / "Scenarios" / argv[2] / "Flooding" / "simulations" / "wflow_event"
sfincs_out_path = database.output_path / "Scenarios" / argv[2] / "Flooding" / "simulations" / "overland"

sfincs_path = database.static_path / "templates" / database.site.attrs.sfincs.overland_model

start_time = datetime.strptime(scenario['event']['stasrt_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario['event']['end_time'],"%Y-%m-%d %H:%M:%S")

print("Reading base SFINCS model")

sf = SfincsModel(
    root=sfincs_path,
    mode='r',
    data_catalog=scenario['event']['data_catalogues']
)
sf.set_root(sfincs_out_path, mode='w+')

print("Set SFINCS timing and forcing")
sf.setup_config(
    **{
        "tref": datetime.strftime(start_time, "%Y%m%d %H%M%"),
        "tstart": datetime.strftime(start_time, "%Y%m%d %H%M%"),
        "tstop": datetime.strftime(end_time, "%Y%m%d %H%M%"),
    }
)

sf.setup_waterlevel_forcing(geodataset=scenario['event']['sfincs_forcing']['waterlevel'],buffer=2000)

sf.setup_precip_forcing_from_grid(precip=scenario['event']['sfincs_forcing']['meteo'], aggregate=False)
sf.setup_wind_forcing_from_grid(scenario['event']['sfincs_forcing']['meteo'])
sf.setup_pressure_forcing_from_grid(scenario['event']['sfincs_forcing']['meteo'])

print("Write SFINCS to output folder")
sf.write()

print(f"Updating SFINCS model for Scenario {argv[2]} with discharge from WFLOW model at {str(wflow_path)}")

logger = setuplog("Update overland SFINCS", log_level=10)
wf = WflowModel(
    root=wflow_path,
    mode="r",
    logger=logger
)
wf.read()

inp = SfincsInput.from_file(sfincs_out_path/"sfincs.inp")
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
inp.write(inp_fn=sfincs_out_path/"sfincs.inp")


