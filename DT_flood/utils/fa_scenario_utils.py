"""Utils functions for setting up FloodAdapt objects."""

import os
from pathlib import Path
from typing import Union

import geopandas as gpd
import hydromt  # noqa: F401
import pandas as pd
import tomli
from flood_adapt.api import events, measures, projections, scenarios, static, strategies
from flood_adapt.dbs_classes.interface.database import IDatabase
from flood_adapt.misc.config import Settings, UnitSystem
from flood_adapt.object_model.hazard.forcing import rainfall, wind
from flood_adapt.object_model.hazard.interface.events import IEvent
from flood_adapt.object_model.interface.projections import IProjection
from flood_adapt.object_model.interface.scenarios import IScenario
from flood_adapt.object_model.interface.strategies import IStrategy

from DT_flood.utils.data_utils import (
    get_dataset_names,
    get_event_forcing_data,
    get_gtsm_forcing_data,
)


def tree(directory):
    """Print the folder structure of a directory."""
    print(f"+ {directory}")
    for path in sorted(directory.rglob("*")):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")


def folder_structure(root: Path):
    """Create FloodAdapt database folder structure (copied from FA database_builder)."""
    input_folder = root / "input"
    static_folder = root / "static"

    inputs = [
        "events",
        "projections",
        "measures",
        "strategies",
        "scenarios",
        "benefits",
    ]
    folder = ["templates"]

    input_folder.mkdir()
    for name in inputs:
        (input_folder / name).mkdir()
    static_folder.mkdir()
    for name in folder:
        (static_folder / name).mkdir()


def create_systems_folder(database_path: Path):
    """Create the systems folder with empty files to get around FA model executable validation."""
    systems_path = database_path / "system"
    fiat_path = systems_path / "fiat" / "fiat"
    sfincs_path = systems_path / "sfincs" / "sfincs"

    systems_path.mkdir(parents=True)
    fiat_path.parent.mkdir(parents=True)
    fiat_path.touch()
    sfincs_path.parent.mkdir(parents=True)
    sfincs_path.touch()


def init_scenario(
    database_path: Union[str, os.PathLike], scenario_name: str
) -> tuple[IDatabase, dict]:
    """Fetch topmost objects for configuration.

    Parameters
    ----------
    database_path : Union[str, os.PathLike]
        Path to FloodAdapt database. Note: Convention here is different from FloodAdapt API.
        Points to a single database, with path including the database/site name
    scenario_config_name : str
        Name of toplevel config file. Looked for in database_path folder

    Returns
    -------
    tuple[IDatabase, dict]
        db : IDatabase
            FloodAdapt Database object
        scenario : dict
            Dictionary containing scenario configuration parameters
    """
    if isinstance(database_path, str):
        database_path = Path(database_path)

    scenario_path = (
        database_path
        / "input"
        / "scenarios"
        / scenario_name
        / (scenario_name + "_toplevel.toml")
    )

    units = UnitSystem(system="metric")

    if not (database_path / "system").exists():
        create_systems_folder(database_path)

    Settings(
        DATABASE_ROOT=database_path.parent,
        DATABASE_NAME=database_path.stem,
        SYSTEM_FOLDER=database_path / "system",
        DELETE_CRASHED_RUNS=False,
        unit_system=units,
        VALIDATE_ALLOWED_FORCINGS=False,
    )
    db = static.read_database(
        database_path=database_path.parent, site_name=database_path.stem
    )
    with open(scenario_path, "rb") as f:
        scenario = tomli.load(f)

    return db, scenario


def create_scenario_config(database: IDatabase, scenario_config: dict) -> IScenario:
    """Create FloodAdapt Scenario object from scenario configuration."""
    scenario_dict = {
        "name": scenario_config["name"],
        "description": f"Scenario generated from toplevel {scenario_config['name']} config file",
        "event": scenario_config["event"]["name"],
        "projection": scenario_config["projection"]["name"],
        "strategy": scenario_config["strategy"]["name"],
    }
    return scenarios.create_scenario(attrs=scenario_dict)


def create_scenario(database: IDatabase, scenario_config: dict) -> IScenario:
    """Check if scenario already exists.

    If not, create it and save config file. If yes, return Scenario object of pre-existing event config.

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IScenario
        FloodAdapt Scenario object
    """
    # Create Event, Projection, Strategy used in scenario
    _ = create_event(database=database, scenario_config=scenario_config)
    _ = create_projection(database=database, scenario_config=scenario_config)
    _ = create_strategy(database=database, scenario_config=scenario_config)

    # Load existing scenarios
    scenarios_existing = scenarios.get_scenarios()

    # If necessary create new scenario, save it and return object, otherwise load existing and return object
    if scenario_config["name"] not in scenarios_existing["name"]:
        scenario_new = create_scenario_config(database, scenario_config)
        scenarios.save_scenario(scenario_new)
        return scenario_new
    else:
        return scenarios.get_scenario(scenario_config["name"])


def create_event(database: IDatabase, scenario_config: dict) -> IEvent:
    """Check if event already exists.

    If not, create it and save config file. If yes, return Event object of pre-existing event config

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IEvent
        FloodAdapt Event object
    """
    # Load existing events
    events_existing = events.get_events()
    # If necessary create new event, save it and return object, otherwise load existing and return object
    if scenario_config["event"]["name"] not in events_existing["name"]:
        event_new = create_event_config(database, scenario_config)
        events.save_event(event_new)
        return event_new
    else:
        return events.get_event(scenario_config["event"]["name"])


def create_event_config(database: IDatabase, scenario_config: dict) -> IEvent:
    """Create FloodAdapt Event object from scenario configuration.

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IEvent
        FloodAdapt Event object of Event created from scenario config

    Raises
    ------
    NotImplementedError
        Only supports HistoricalNearshore event types
    """
    forcing_vars = {
        "meteo": ["precip", "wind10_u", "wind10_v", "press_msl"],
        "wind": ["wind10_u", "wind10_v"],
        "rainfall": ["precip"],
        "waterlevel": ["waterlevel"],
        "wflow": ["kin", "kout", "temp", "press_msl", "precip"],
        "orography": ["elevtn"],
    }

    units = UnitSystem("metric")

    start_time = scenario_config["event"]["start_time"]
    end_time = scenario_config["event"]["end_time"]

    start_warmup = (pd.to_datetime(start_time) - pd.DateOffset(years=1)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    event_name = scenario_config["event"]["name"]

    sf_bounds = database.static.get_model_boundary().to_crs(4326).total_bounds
    wf_bounds = (
        gpd.read_file(
            database.static_path
            / "templates"
            / "wflow"
            / "staticgeoms"
            / "region.geojson"
        )
        .to_crs(4326)
        .total_bounds
    )

    dataset_names = get_dataset_names()

    event_folder = database.base_path / "input" / "events" / event_name
    if not event_folder.exists():
        event_folder.mkdir(parents=True)

    data_folder = database.base_path / "data" / event_name
    if not data_folder.exists():
        data_folder.mkdir(parents=True)

    forcings = {}

    # Get SFINCS forcing data
    for forcing in scenario_config["event"]["sfincs_forcing"]:
        if forcing not in forcing_vars:
            print(f"Warning: {forcing} not in forcing_vars, skipping {forcing}")
            continue
        if scenario_config["event"]["sfincs_forcing"][forcing] not in dataset_names:
            raise ValueError(
                f"Dataset {scenario_config['event']['sfincs_forcing'][forcing]} not in dataset names: {dataset_names}"
            )
        print(f"Getting {forcing} data")
        if "waterlevel" in forcing:
            ds = get_gtsm_forcing_data(
                dataset=scenario_config["event"]["sfincs_forcing"][forcing],
                start_date=start_time,
                end_date=end_time,
                data_vars=forcing_vars[forcing],
                bounds=sf_bounds,
            )
            ds.to_netcdf(event_folder / f"{forcing}.nc")
        else:
            ds = get_event_forcing_data(
                dataset=scenario_config["event"]["sfincs_forcing"][forcing],
                start_date=start_time,
                end_date=end_time,
                data_vars=forcing_vars[forcing],
                bounds=sf_bounds,
            )
            if "latitude" in ds.coords:
                ds = ds.rename({"latitude": "lat"})
            if "longitude" in ds.coords:
                ds = ds.rename({"longitude": "lon"})
            ds.to_netcdf(data_folder / f"{forcing}.nc")

    # Get WFlow forcing data
    for forcing in scenario_config["event"]["wflow_forcing"]:
        if scenario_config["event"]["wflow_forcing"][forcing] not in dataset_names:
            raise ValueError(
                f"Dataset {scenario_config['event']['wflow_forcing'][forcing]} not in dataset names: {dataset_names}"
            )
        print(f"Getting {forcing} data")
        print(
            forcing_vars["wflow"]
            if "orography" not in forcing
            else forcing_vars["orography"]
        )
        ds = get_event_forcing_data(
            dataset=scenario_config["event"]["wflow_forcing"][forcing],
            start_date=start_warmup if "warmup" in forcing else start_time,
            end_date=start_time if "warmup" in forcing else end_time,
            data_vars=forcing_vars["wflow"]
            if "orography" not in forcing
            else forcing_vars["orography"],
            bounds=wf_bounds,
        )

        ds.to_netcdf(event_folder / f"{forcing}.nc")

    # # Set meteo forcing type
    # if scenario_config["event"]["data_catalogues"]:
    #     dc = DataCatalog(scenario_config["event"]["data_catalogues"])

    #     if "meteo" in scenario_config["event"]["sfincs_forcing"].keys():
    #         meteo_key = scenario_config["event"]["sfincs_forcing"]["meteo"]
    #         ds = dc.get_rasterdataset(meteo_key, time_tuple=(start_time, end_time))
    #         meteo_fn = data_folder / "meteo.nc"
    #         ds.to_netcdf(meteo_fn)
    #         shutil.copy(meteo_fn, event_folder / "meteo.nc")
    #     if "wind" in scenario_config["event"]["sfincs_forcing"].keys():
    #         wind_key = scenario_config["event"]["sfincs_forcing"]["wind"]
    #         ds = dc.get_rasterdataset(wind_key, time_tuple=(start_time, end_time))
    #         wind_fn = data_folder / "wind.nc"
    #         ds.to_netcdf(wind_fn)
    #         shutil.copy(wind_fn, event_folder / "wind.nc")
    #     if "rainfall" in scenario_config["event"]["sfincs_forcing"].keys():
    #         rainfall_key = scenario_config["event"]["sfincs_forcing"]["rainfall"]
    #         ds = dc.get_rasterdataset(rainfall_key, time_tuple=(start_time, end_time))
    #         rain_fn = data_folder / "rainfall.nc"
    #         ds.to_netcdf(rain_fn)
    #         shutil.copy(rain_fn, event_folder / "rainfall.nc")
    # else:
    #     if "meteo" in scenario_config["event"]["sfincs_forcing"].keys():
    #         meteo_fn = scenario_config["event"]["sfincs_forcing"]["meteo"]

    #     if "wind" in scenario_config["event"]["sfincs_forcing"].keys():
    #         wind_fn = scenario_config["event"]["sfincs_forcing"]["wind"]

    #     if "rainfall" in scenario_config["event"]["sfincs_forcing"].keys():
    #         rain_fn = scenario_config["event"]["sfincs_forcing"]["rainfall"]

    if (data_folder / "meteo.nc").exists():
        wind_forcing = wind.WindNetCDF(
            unit=units.velocity, path=data_folder / "meteo.nc"
        )
        rain_forcing = rainfall.RainfallNetCDF(
            unit=units.intensity, path=data_folder / "meteo.nc"
        )
        forcings["WIND"] = [wind_forcing]
        forcings["RAINFALL"] = [rain_forcing]
    if (data_folder / "wind.nc").exists():
        wind_forcing = wind.WindNetCDF(unit=units.velocity, path="wind.nc")
        forcings["WIND"] = [wind_forcing]
    if (data_folder / "rainfall.nc").exists():
        rain_forcing = rainfall.RainfallNetCDF(unit=units.intensity, path="rainfall.nc")

    event_dict = {
        "name": event_name,
        "time": {
            "start_time": start_time,
            "end_time": end_time,
        },
        "template": "Historical",
        "mode": "single_event",
        "forcings": forcings,
    }

    # if "waterlevel" in scenario_config["event"]["sfincs_forcing"]:
    #     waterlevel_key = scenario_config["event"]["sfincs_forcing"]["waterlevel"]
    #     ds = dc.get_geodataset(waterlevel_key, time_tuple=(start_time, end_time))
    #     ds.to_netcdf(event_folder / "waterlevel.nc")

    return events.create_event(attrs=event_dict)


def create_projection(database: IDatabase, scenario_config: dict) -> IProjection:
    """Check if projection already exists.

    If not, create it and save config file. If yes, return Projection object of pre-existing projection config

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IProjection
        FloodAdapt Projection object
    """
    # Load existing projections
    projections_existing = projections.get_projections()

    # If necessary create new projection, save it and return object, otherwise load existing and return object
    if scenario_config["projection"]["name"] not in projections_existing["name"]:
        projection_new = create_projection_config(database, scenario_config)
        projections.save_projection(projection_new)
        return projection_new
    else:
        return projections.get_projection(scenario_config["projection"]["name"])


def create_projection_config(database: IDatabase, scenario_config: dict) -> IProjection:
    """Create FloodAdapt Projection object from scenario configuration.

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IProjection
        FloodAdapt Projection object
    """
    # General projection config
    projection_dict = {
        "name": scenario_config["projection"]["name"],
        "description": f"Projection generated from toplevel {scenario_config['name']} config file",
    }

    # Physical projection config
    phys_dict = {}
    for name in scenario_config["projection"]["physical_projection"]:
        if name == "sea_level_rise" or name == "subsidence":
            phys_dict.update(
                {
                    name: {
                        "value": scenario_config["projection"]["physical_projection"][
                            name
                        ],
                        "units": "meters",
                    }
                }
            )
        else:
            phys_dict.update(
                {name: scenario_config["projection"]["physical_projection"][name]}
            )
    projection_dict.update({"physical_projection": phys_dict})

    # Socio-Economic config
    sec_dict = {}
    for name in scenario_config["projection"]["socio_economic_change"]:
        if name == "new_development_elevation":
            sec_dict.update(
                {
                    name: {
                        "value": scenario_config["projection"]["socio_economic_change"][
                            name
                        ],
                        "units": "meters",
                    }
                }
            )
        else:
            sec_dict.update(
                {name: scenario_config["projection"]["socio_economic_change"][name]}
            )
    projection_dict.update({"socio_economic_change": sec_dict})

    return projections.create_projection(attrs=projection_dict)


def create_strategy(database: IDatabase, scenario_config: dict) -> IStrategy:
    """Check if strategy already exists.

    If not, create it and save config file. If yes, return Strategy object of pre-existing strategy config

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IStrategy
        FloodAdapt Strategy object
    """
    # Load existing strategies
    strategies_existing = strategies.get_strategies()

    # If necessary create new strategy, save it and return object, otherwise load existing and return object
    if scenario_config["strategy"]["name"] not in strategies_existing["name"]:
        strategy_new = create_strategy_config(database, scenario_config)
        strategies.save_strategy(strategy_new)
        return strategy_new
    else:
        return strategies.get_strategy(scenario_config["strategy"]["name"])


def create_strategy_config(database: IDatabase, scenario_config: dict) -> IStrategy:
    """Create FloodAdapt Strategy object from scenario configuration.

    Where necessary create new measures, otherwise use existing ones.

    Parameters
    ----------
    database : IDatabase
        FloodAdapt Database object
    scenario_config : dict
        Dict containing toplevel scenario configurations

    Returns
    -------
    IStrategy
        FloodAdapt Strategy object
    """
    # General scenario config
    scenario_dict = {
        "name": scenario_config["strategy"]["name"],
        "description": f"Strategy generated from toplevel {scenario_config['name']} config file",
    }
    measure_list = []
    # measures_existing = measures.get_measures(database)
    measures_existing = measures.get_measures()
    for measure in scenario_config["strategy"]:
        if "measure" not in measure:
            continue

        measure_list.append(scenario_config["strategy"][measure]["name"])
        if (
            scenario_config["strategy"][measure]["name"]
            not in measures_existing["name"]
        ):
            measure_dict = {}
            measure_dict.update(
                {
                    "name": scenario_config["strategy"][measure]["name"],
                    "type": scenario_config["strategy"][measure]["type"],
                }
            )

            if Path(scenario_config["strategy"][measure]["selection"]).exists():
                selection_type = "polygon"
                polygon_file = scenario_config["strategy"][measure]["selection"]
                measure_dict.update({"polygon_file": polygon_file})
            elif scenario_config["strategy"][measure]["selection"] == "all":
                selection_type = "all"
            else:
                selection_type = "aggregation_area"

            measure_dict.update({"selection_type": selection_type})
            measure_dict.update(scenario_config["strategy"][measure]["misc"])
            measure_new = measures.create_measure(
                attrs=measure_dict, type=scenario_config["strategy"][measure]["type"]
            )
            measures.save_measure(measure_new)

    scenario_dict.update({"measures": measure_list})
    return strategies.create_strategy(attrs=scenario_dict)
