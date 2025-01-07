from pathlib import Path
from sys import argv
from datetime import datetime
from shutil import copytree
import tomli

from hydromt.log import setuplog
from hydromt_wflow import WflowModel
from hydromt_sfincs import SfincsModel
from hydromt_sfincs.sfincs_input import SfincsInput
from DT_flood.utils.fa_scenario_utils import init_scenario

def tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")

database, scenario_config = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))
scenario = database.scenarios.get(scenario_config["name"])

# db_path = Path(argv[1])
# output_path = db_path / Path(f"output/scenarios/{argv[2]}/Flooding/simulations")
# static_path = db_path / Path("static/templates")
# scenario_fn = db_path / (argv[2]+"_toplevel.toml")



# wflow_path = output_path/"wflow_event"
# sfincs_out_path = output_path/"overland"
wflow_path = scenario.results_path / "Flooding" / "simulations" / "wflow_event"
sfincs_out_path = scenario.results_path / "Flooding" / "simulations" / "overland"
# wflow_path = database.output_path / "Scenarios" / argv[2] / "Flooding" / "simulations" / "wflow_event"
# sfincs_out_path = database.output_path / "Scenarios" / argv[2] / "Flooding" / "simulations" / "overland"

# sfincs_path = static_path/"overland"
sfincs_path = database.static_path / "templates" / database.site.attrs.sfincs.overland_model

# with open(scenario_fn, 'rb') as f:
#     scenario_config = tomli.load(f)

print(f"FA database: \n")
tree(Path(argv[1]))
print(f"wflow folder: {wflow_path}")
tree(wflow_path)
print(f"sfincs static: {sfincs_path}")
tree(sfincs_path)
print(f"sfincs output path: {sfincs_out_path}")
tree(sfincs_out_path)

start_time = datetime.strptime(scenario_config['event']['start_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario_config['event']['end_time'],"%Y-%m-%d %H:%M:%S")

print("Copying SFINCS files")
copytree(sfincs_path, sfincs_out_path, dirs_exist_ok=True)

print("Reading base SFINCS model")

sf = SfincsModel(
    root=sfincs_out_path,
    mode='r',
    data_libs=scenario_config['event']['data_catalogues']
)
sf.read()
# sf.set_root(sfincs_out_path, mode='w+')

print("Set SFINCS timing and forcing")
sf.setup_config(
    **{
        "tref": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstart": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstop": datetime.strftime(end_time, "%Y%m%d %H%M%S"),
    }
)

sf.setup_waterlevel_forcing(geodataset=scenario_config['event']['sfincs_forcing']['waterlevel'],buffer=2000)

meteo = sf.data_catalog.get_rasterdataset(scenario_config['event']['sfincs_forcing']['meteo'],geom=sf.region,time_tuple=sf.get_model_time())

sf.setup_precip_forcing_from_grid(precip=meteo['precip'], aggregate=False)
sf.setup_wind_forcing_from_grid(wind=meteo.rename({"wind10_u": "wind_u", "wind10_v": "wind_v"}))
sf.setup_pressure_forcing_from_grid(press=meteo['press_msl'])

print("Write SFINCS to output folder")
sf.write_forcing()
sf.write_config()

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

database.shutdown()
