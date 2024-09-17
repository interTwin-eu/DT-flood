from pathlib import Path
from sys import argv
from datetime import datetime
from shutil import copytree

from hydromt.log import setuplog
from hydromt.exceptions import NoDataException
from hydromt_wflow import WflowModel
from hydromt_sfincs import SfincsModel
from hydromt_sfincs.sfincs_input import SfincsInput
from DT_flood.utils.fa_scenario_utils import init_scenario

database, scenario = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))

sfincs_out_path = database.output_path / "Scenarios" / argv[2] / "Flooding" / "simulations" / "overland"

sfincs_path = database.static_path / "templates" / database.site.attrs.sfincs.overland_model

start_time = datetime.strptime(scenario['event']['start_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario['event']['end_time'],"%Y-%m-%d %H:%M:%S")

print("Copying SFINCS files")
copytree(sfincs_path, sfincs_out_path, dirs_exist_ok=True)

print("Reading base SFINCS model")

sf = SfincsModel(
    root=sfincs_out_path,
    mode='r',
    data_libs=scenario['event']['data_catalogues']
)
sf.read()

print("Set SFINCS timing and forcing")
sf.setup_config(
    **{
        "tref": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstart": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstop": datetime.strftime(end_time, "%Y%m%d %H%M%S"),
    }
)

sf.setup_waterlevel_forcing(geodataset=scenario['event']['sfincs_forcing']['waterlevel'],buffer=2000)

try:
    meteo = sf.data_catalog.get_rasterdataset(scenario['event']['sfincs_forcing']['meteo'],geom=sf.region.to_crs(4326),time_tuple=sf.get_model_time())
except NoDataException:
    meteo = sf.data_catalog.get_rasterdataset(scenario['event']['sfincs_forcing']['meteo'],geom=sf.region.to_crs(4326),time_tuple=sf.get_model_time(), buffer=1)
except:
    print("Failed to get SFINCS Meteo data")
    


sf.setup_precip_forcing_from_grid(precip=meteo['precip'], aggregate=False)

print("Write SFINCS to output folder")
sf.write_forcing()
sf.write_config()

