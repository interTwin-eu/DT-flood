"""Utils functions for setting up FloodAdapt objects."""

import os
from pathlib import Path
from typing import Union

import geopandas as gpd
import hydromt  # noqa: F401
import pandas as pd
import tomli
from flood_adapt.config.config import Settings
from flood_adapt.dbs_classes.interface.database import IDatabase
from flood_adapt.flood_adapt import FloodAdapt
from flood_adapt.objects.forcing import rainfall, wind

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

    if not (database_path / "system").exists():
        create_systems_folder(database_path)

    Settings(
        DATABASE_ROOT=database_path.parent,
        DATABASE_NAME=database_path.stem,
        SYSTEM_FOLDER=database_path / "system",
        DELETE_CRASHED_RUNS=False,
        VALIDATE_ALLOWED_FORCINGS=False,
    )
    db = FloodAdapt(database_path=database_path)

    with open(scenario_path, "rb") as f:
        scenario = tomli.load(f)

    return db, scenario


def create_scenario_config(database: FloodAdapt, scenario_config: dict):
    """Create FloodAdapt Scenario object from scenario configuration."""
    scenario_dict = {
        "name": scenario_config["name"],
        "description": f"Scenario generated from toplevel {scenario_config['name']} config file",
        "event": scenario_config["event"]["name"],
        "projection": scenario_config["projection"]["name"],
        "strategy": scenario_config["strategy"]["name"],
    }
    return database.create_scenario(attrs=scenario_dict)


def create_scenario(database: FloodAdapt, scenario_config: dict):
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
    scenarios_existing = database.get_scenarios()

    # If necessary create new scenario, save it and return object, otherwise load existing and return object
    if scenario_config["name"] not in scenarios_existing["name"]:
        scenario_new = create_scenario_config(database, scenario_config)
        database.save_scenario(scenario_new)
        return scenario_new
    else:
        return database.get_scenario(scenario_config["name"])


def create_event(database: FloodAdapt, scenario_config: dict):
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
    events_existing = database.get_events()
    # If necessary create new event, save it and return object, otherwise load existing and return object
    if scenario_config["event"]["name"] not in events_existing["name"]:
        event_new = create_event_config(database, scenario_config)
        database.save_event(event_new)
        return event_new
    else:
        return database.get_event(scenario_config["event"]["name"])


def create_event_config(database: FloodAdapt, scenario_config: dict):
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

    # units = UnitSystems("metric")
    units = database.database.site.gui.units

    start_time = scenario_config["event"]["start_time"]
    end_time = scenario_config["event"]["end_time"]

    start_warmup = (pd.to_datetime(start_time) - pd.DateOffset(years=1)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    event_name = scenario_config["event"]["name"]

    sf_bounds = database.get_model_boundary().to_crs(4326).total_bounds
    wf_bounds = (
        gpd.read_file(
            database.database.static_path
            / "templates"
            / "wflow"
            / "staticgeoms"
            / "region.geojson"
        )
        .to_crs(4326)
        .total_bounds
    )

    dataset_names = get_dataset_names()

    event_folder = database.database.base_path / "input" / "events" / event_name
    if not event_folder.exists():
        event_folder.mkdir(parents=True)

    data_folder = database.database.base_path / "data" / event_name
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

    if (data_folder / "meteo.nc").exists():
        wind_forcing = wind.WindNetCDF(
            unit=units.default_velocity_units, path=data_folder / "meteo.nc"
        )
        rain_forcing = rainfall.RainfallNetCDF(
            unit=units.default_intensity_units, path=data_folder / "meteo.nc"
        )
        forcings["WIND"] = [wind_forcing]
        forcings["RAINFALL"] = [rain_forcing]
    if (data_folder / "wind.nc").exists():
        wind_forcing = wind.WindNetCDF(
            unit=units.default_velocity_units, path="wind.nc"
        )
        forcings["WIND"] = [wind_forcing]
    if (data_folder / "rainfall.nc").exists():
        rain_forcing = rainfall.RainfallNetCDF(
            unit=units.default_intensity_units, path="rainfall.nc"
        )

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

    return database.create_event(attrs=event_dict)


def create_projection(database: FloodAdapt, scenario_config: dict):
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
    projections_existing = database.get_projections()

    # If necessary create new projection, save it and return object, otherwise load existing and return object
    if scenario_config["projection"]["name"] not in projections_existing["name"]:
        projection_new = create_projection_config(database, scenario_config)
        database.save_projection(projection_new)
        return projection_new
    else:
        return database.get_projection(scenario_config["projection"]["name"])


def create_projection_config(database: FloodAdapt, scenario_config: dict):
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

    return database.create_projection(attrs=projection_dict)


def create_strategy(database: FloodAdapt, scenario_config: dict):
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
    strategies_existing = database.get_strategies()

    # If necessary create new strategy, save it and return object, otherwise load existing and return object
    if scenario_config["strategy"]["name"] not in strategies_existing["name"]:
        strategy_new = create_strategy_config(database, scenario_config)
        database.save_strategy(strategy_new)
        return strategy_new
    else:
        return database.get_strategy(scenario_config["strategy"]["name"])


def create_strategy_config(database: FloodAdapt, scenario_config: dict):
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
    measures_existing = database.get_measures()
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
            measure_new = database.create_measure(
                attrs=measure_dict, type=scenario_config["strategy"][measure]["type"]
            )
            database.save_measure(measure_new)

    scenario_dict.update({"measures": measure_list})
    return database.create_strategy(attrs=scenario_dict)
