from sys import argv
from pathlib import Path
from datetime import datetime, timedelta
from shutil import copytree
import xarray as xr
import pandas as pd
from hydromt_sfincs import SfincsModel

from DT_flood.utils.fa_scenario_utils import init_scenario
from DT_flood.utils.sfincs_utils import (
    read_flow_boundary_points,
    read_astro_boundary_conditions,
    generate_bzs_from_bca,
    process_dt_climate,
)

database, scenario_config = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))
scenario = database.scenarios.get(scenario_config["name"])

sf_template =  database.static_path / "templates" / database.site.attrs.sfincs.offshore_model
sfincs_out_path = scenario.results_path/"Flooding"/"simulations"/"offshore"

start_time = datetime.strptime(scenario_config['event']['start_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario_config['event']['end_time'],"%Y-%m-%d %H:%M:%S")

# move start time back 4 days to let the waterlevel propagate from edges of offshore model to the centre
start_time = start_time - timedelta(days=3)

meteo_fn = scenario_config['event']['sfincs_forcing_offshore']

tidemodel = "GTSMv4.1_opendap"
complist=['2N2','J1','K1','K2','L2','M1','M2','M3','M4','MF','MM','MSF','MU2','N2','NU2','O1','OO1','P1','Q1','R2','S1','S2','SA','SSA','T2']

print("Creating event offshore folder")
copytree(sf_template, sfincs_out_path, dirs_exist_ok=True)

print("Reading SFINCS model")
sf = SfincsModel(
    root=sfincs_out_path,
    mode='r'
)
sf.read()

sf.setup_config(
    **{
        "tref": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstart": datetime.strftime(start_time, "%Y%m%d %H%M%S"),
        "tstop": datetime.strftime(end_time, "%Y%m%d %H%M%S")
    }
)

print(f"SFINCS timing set to:\ntstart: {sf.config['tstart']}\ntstop: {sf.config['tstop']}")

print("Processing DT Climate data")
if Path(meteo_fn).suffix == ".grib":
    ds = process_dt_climate(
        filepath=meteo_fn,
        tstart=start_time,
        tend=end_time,
        bounds=sf.region.bounds.iloc[0].values
    )
elif Path(meteo_fn).suffix == ".nc":
    ds = xr.open_dataset(meteo_fn)
else:
    ValueError("Provide data in correct format.")

sf.setup_pressure_forcing_from_grid(press=ds['press_msl'])
sf.setup_wind_forcing_from_grid(wind=ds[['wind10_u', 'wind10_v']])

sf.write_forcing()
sf.write_config()

print("Setting up tidal forcing")

print("Removing old bzs file")
(Path(sf.root)/"sfincs.bzs").unlink()
flow_bounds = read_flow_boundary_points(Path(sf.root)/"sfincs.bnd")
flow_bounds = read_astro_boundary_conditions(flow_boundary_point=flow_bounds, bca_fn=Path(sf.root)/f"tide_{tidemodel}.bc")
bzs = generate_bzs_from_bca(
    flow_boundary_point=flow_bounds,
    tref=start_time,
    tstart=start_time,
    tstop=end_time,
    bzs_fn=Path(sf.root)/"sfincs.bzs",
    write_file=False
)
bzs.to_csv(
    Path(sf.root)/"sfincs.bzs",
    index=True,
    sep=" ",
    header=False,
    float_format="%0.3f"
)
print(f"Written tidal timeseries to {sf.root}/sfincs.bzs")