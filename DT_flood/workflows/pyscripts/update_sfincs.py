from pathlib import Path
from sys import argv
from datetime import datetime
from shutil import copytree
import xarray as xr
import pandas as pd
import geopandas as gpd

from hydromt.log import setuplog
from hydromt.exceptions import NoDataException
from hydromt_sfincs import SfincsModel
from hydromt_sfincs.sfincs_input import SfincsInput
from DT_flood.utils.fa_scenario_utils import init_scenario
from flood_adapt.api import events
from flood_adapt.adapter.sfincs_adapter import SfincsAdapter

database, scenario_config = init_scenario(argv[1], (argv[2]+"_toplevel.toml"))
scenario = database.scenarios.get(scenario_config['name'])
event = events.get_event(scenario_config['event']['name'])

sfincs_out_path = scenario.results_path/"Flooding"/"simulations"/"overland"

sfincs_path = database.static_path / "templates" / database.site.attrs.sfincs.overland_model

start_time = datetime.strptime(scenario_config['event']['start_time'],"%Y-%m-%d %H:%M:%S")
end_time = datetime.strptime(scenario_config['event']['end_time'],"%Y-%m-%d %H:%M:%S")

print("Copying SFINCS files")
copytree(sfincs_path, sfincs_out_path, dirs_exist_ok=True)

print("Reading base SFINCS model")

sf = SfincsModel(
    root=sfincs_out_path,
    mode='r+',
    data_libs=scenario_config['event']['data_catalogues']
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

if event.attrs.template == "Historical_nearshore":
    sf.setup_waterlevel_forcing(geodataset=scenario_config['event']['sfincs_forcing']['waterlevel'],buffer=2000)
elif event.attrs.template == "Historical_offshore":
    print("Setting up overland waterlevels from offshore model outputs")
    offshore_his_fn =  scenario.results_path/"Flooding"/"simulations"/"offshore"/"sfincs_his.nc"
    offshore_his = xr.open_dataset(offshore_his_fn)

    bnd_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(offshore_his['station_x'].values, offshore_his['station_y'].values),
        crs=4326
    )
    timeseries = pd.DataFrame(
        data=offshore_his['point_h'].values,
        columns=[str(x) for x in bnd_points.index],
        index=offshore_his.time.values
    )
    sf.setup_waterlevel_forcing(
        timeseries=timeseries+scenario.direct_impacts.hazard.physical_projection.attrs.sea_level_rise.value,
        locations=bnd_points,
        merge=False)
else:
    ValueError("No valid event type")

if scenario_config['event']['sfincs_forcing']['meteo']:
    try:
        meteo = sf.data_catalog.get_rasterdataset(scenario_config['event']['sfincs_forcing']['meteo'],geom=sf.region.to_crs(4326),time_tuple=sf.get_model_time())
    except NoDataException:
        meteo = sf.data_catalog.get_rasterdataset(scenario_config['event']['sfincs_forcing']['meteo'],geom=sf.region.to_crs(4326),time_tuple=sf.get_model_time(), buffer=1)
    except:
        print("Failed to get SFINCS Meteo data")
    
    sf.setup_precip_forcing_from_grid(
        precip=meteo['precip']
            * (1+scenario.direct_impacts.hazard.physical_projection.attrs.rainfall_increase/100.0),
        aggregate=False)
else:
    print("No overland meteo forcing specified.")

print("Write SFINCS to output folder")
sf.write_forcing()
sf.write_config()

del sf

sf_adapt = SfincsAdapter(model_root=sfincs_out_path, site=database.site)

if scenario.direct_impacts.hazard.hazard_strategy.measures is not None:
    print("Setting up overland measures")
    for measure in scenario.direct_impacts.hazard.hazard_strategy.measures:
        measure_path = database.measures.get_database_path().joinpath(
            measure.attrs.name
        )

        if measure.attrs.type == "floodwall":
            sf_adapt.add_floodwall(
                floodwall=measure.attrs, measure_path=measure_path
            )
        if measure.attrs.type == "pump":
            sf_adapt.add_pump(pump=measure.attrs, measure_apath=measure_path)
        if (
            measure.attrs.type == "greening"
            or measure.attrs.type == "total_storage"
            or measure.attrs.type == "water_square"
        ):
            sf_adapt.add_green_infrastructure(
                green_infrastructure=measure.attrs,
                measure_path=measure_path
            )

sf_adapt.write_sfincs_model(path_out=sfincs_out_path)

del sf_adapt
