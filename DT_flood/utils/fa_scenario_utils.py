"""Utils functions for setting up FloodAdapt objects."""

import os
from pathlib import Path
from typing import Union

import geojson
import geopandas as gpd
import hydromt  # noqa: F401
import pandas as pd
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


def get_database(database_path):
    """Get database object."""
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

    return db


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

    db = get_database(database_path=database_path)
    scenario = db.get_scenario(scenario_name)

    return db, scenario


def create_scenario(
    database: FloodAdapt, name: str, event: str, strategy: str, projection: str
):
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
    if event not in database.get_events()["name"]:
        raise ValueError(f"Event {event} does not exist in the database!")
    if strategy not in database.get_strategies()["name"]:
        raise ValueError(f"Strategy {strategy} does not exist in the database!")
    if projection not in database.get_projections()["name"]:
        raise ValueError(f"Projection {projection} does not exist in the database!")

    # Load existing scenarios
    scenarios_existing = database.get_scenarios()

    # If necessary create new scenario, save it and return object, otherwise load existing and return object
    if name not in scenarios_existing["name"]:
        scenario_new = create_scenario_config(
            database=database,
            name=name,
            event=event,
            strategy=strategy,
            projection=projection,
        )
        database.save_scenario(scenario_new)
        return scenario_new
    else:
        return database.get_scenario(name)


def create_scenario_config(
    database: FloodAdapt, name: str, event: str, strategy: str, projection: str
):
    """Create FloodAdapt Scenario object from scenario configuration."""
    scenario_dict = {
        "name": name,
        "event": event,
        "projection": projection,
        "strategy": strategy,
    }
    return database.create_scenario(attrs=scenario_dict)


def create_event(
    database: FloodAdapt,
    name: str,
    start_time: str,
    end_time: str,
    sf_forcings: dict = None,
    wf_forcings: dict = None,
):
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
    if sf_forcings is None:
        sf_forcings = {"meteo": "era5_hourly", "waterlevel": "gtsm_hourly"}
    if wf_forcings is None:
        wf_forcings = {
            "precip_warmup": "era5_daily",
            "pet_warmup": "era5_daily",
            "precip_event": "era5_hourly",
            "pet_event": "era5_hourly",
            "orography": "era5_orography",
        }
    events_existing = database.get_events()
    # If necessary create new event, save it and return object, otherwise load existing and return object
    if name not in events_existing["name"]:
        event_dict = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "sfincs_forcing": sf_forcings,
            "wflow_forcing": wf_forcings,
        }
        event_new = create_event_config(database, event_dict)
        database.save_event(event_new)
        return event_new
    else:
        return database.get_event(name)


def create_event_config(database: FloodAdapt, event_dict: dict):
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

    units = database.database.site.gui.units

    start_time = event_dict["start_time"]
    end_time = event_dict["end_time"]

    start_warmup = (pd.to_datetime(start_time) - pd.DateOffset(years=1)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    event_name = event_dict["name"]

    sf_forcings = event_dict["sfincs_forcing"]
    wf_forcings = event_dict["wflow_forcing"]

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
    for forcing in sf_forcings:
        if forcing not in forcing_vars:
            print(f"Warning: {forcing} not in forcing_vars, skipping {forcing}")
            continue
        if sf_forcings[forcing] not in dataset_names:
            raise ValueError(
                f"Dataset {sf_forcings[forcing]} not in dataset names: {dataset_names}"
            )
        print(f"Getting {forcing} data")
        if "waterlevel" in forcing:
            ds = get_gtsm_forcing_data(
                dataset=sf_forcings[forcing],
                start_date=start_time,
                end_date=end_time,
                data_vars=forcing_vars[forcing],
                bounds=sf_bounds,
            )
            ds.to_netcdf(event_folder / f"{forcing}.nc")
            del ds
        else:
            ds = get_event_forcing_data(
                dataset=sf_forcings[forcing],
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
            del ds

    # Get WFlow forcing data
    for forcing in wf_forcings:
        if wf_forcings[forcing] not in dataset_names:
            raise ValueError(
                f"Dataset {wf_forcings[forcing]} not in dataset names: {dataset_names}"
            )
        print(f"Getting {forcing} data")
        print(
            forcing_vars["wflow"]
            if "orography" not in forcing
            else forcing_vars["orography"]
        )
        ds = get_event_forcing_data(
            dataset=wf_forcings[forcing],
            start_date=start_warmup if "warmup" in forcing else start_time,
            end_date=start_time if "warmup" in forcing else end_time,
            data_vars=forcing_vars["wflow"]
            if "orography" not in forcing
            else forcing_vars["orography"],
            bounds=wf_bounds,
        )
        ds.to_netcdf(event_folder / f"{forcing}.nc")
        del ds

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


def create_projection(
    database: FloodAdapt,
    name: str,
    sea_level_rise: float = None,
    rainfall_increase: float = None,
    population_growth: float = None,
    economic_growth: float = None,
):
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
    if name not in projections_existing["name"]:
        projection_new = create_projection_config(
            database,
            name=name,
            sea_level_rise=sea_level_rise,
            rainfall_increase=rainfall_increase,
            population_growth=population_growth,
            economic_growth=economic_growth,
        )
        database.save_projection(projection_new)
        return projection_new
    else:
        return database.get_projection(name)


def create_projection_config(
    database: FloodAdapt,
    name: str,
    sea_level_rise: float,
    rainfall_increase: float,
    population_growth: float,
    economic_growth: float,
):
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
        "name": name,
        "description": f"Projection generated from toplevel {name} config file",
    }

    # Physical projection config
    phys_dict = {}
    if sea_level_rise is not None:
        phys_dict.update(
            {
                "sea_level_rise": {
                    "value": sea_level_rise,
                    "units": database.database.site.gui.units.default_length_units,
                }
            }
        )
    if rainfall_increase is not None:
        phys_dict.update({"rainfall_increase": rainfall_increase})
    projection_dict.update({"physical_projection": phys_dict})

    # Socio-Economic config
    sec_dict = {}

    if population_growth is not None:
        sec_dict.update({"population_growth_existing": population_growth})
    if economic_growth is not None:
        sec_dict.update({"economic_growth": economic_growth})
    projection_dict.update({"socio_economic_change": sec_dict})

    return database.create_projection(attrs=projection_dict)


def create_measure(
    database: FloodAdapt,
    name: str,
    measure_type: str,
    selection: list[dict],
    value: Union[float, list[float]],
    property_type: str = None,
):
    """Create FloodAdapt Measure object from description.

    If the measure already exists, return existing object.
    Otherwise create new measure.

    Parameters
    ----------
    database : FloodAdapt
        FloodAdapt object
    name : str
        measure name
    measure_type : str
        measure type
    selection : list[dict]
        measure area selection
    value : Union[float, list[float]]
        measure parameter values
    property_type : str, optional
        affected type of property when relevant, by default None

    Returns
    -------
    _type_
        _description_
    """
    measures_existing = database.get_measures()

    if name not in measures_existing["name"]:
        # unpack selected geom singleton list
        # catch empty list (=no selection made)
        try:
            [geom] = selection
        except ValueError:
            geom = None
        measure_new = create_measure_config(
            database=database,
            name=name,
            measure_type=measure_type,
            value=value,
            property_type=property_type,
            geom=geom,
        )
        database.save_measure(measure_new)
        return measure_new
    else:
        return database.get_measure(name)


def create_measure_config(
    database: FloodAdapt,
    name: str,
    measure_type: str,
    geom: dict,
    value: Union[float, list[float]],
    property_type: str = None,
):
    """Create new FloodAdapt measure object from description.

    Parameters
    ----------
    database : FloodAdapt
        FloodAdapt object
    name : str
        measure name
    measure_type : str
        measure type
    geom : dict
        measure area selection
    value : Union[float, list[float]]
        measure parameter values
    property_type : str, optional
        affected type of property when relevant, by default None

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    ValueError
        _description_
    """
    aggregation_area_type = None
    aggregation_area_name = None
    if geom is None:
        selection_type = "all"
        # aggregation_area_type = "all"
    elif "agg_type" in geom:
        selection_type = "aggregation_area"
        aggregation_area_type = geom["agg_type"]
        aggregation_area_name = geom["area_name"]
    elif geom["type"] == "LineString":
        selection_type = "polyline"
    else:
        selection_type = "polygon"

    if measure_type in [
        "floodwall",
        "thin_dam",
        "levee",
        "elevate_properties",
        "floodproof_properties",
    ]:
        if not isinstance(value, float):
            raise ValueError(f"Invalid value {value} for measure type {measure_type}")
        value_dict = {
            "elevation": {
                "value": value,
                "units": database.database.site.gui.units.default_length_units,
            }
        }
        if measure_type in ["floodproof_properties", "elevate_properties"]:
            if property_type not in ["residential", "commercial"]:
                raise ValueError(
                    f"Invalid property type {property_type} for measure type {measure_type}"
                )
            value_dict["property_type"] = property_type
    elif measure_type in ["pump", "culvert"]:
        if not isinstance(value, float):
            raise ValueError(f"Invalid value {value} for measure type {measure_type}")
        value_dict = {
            "discharge": {
                "value": value,
                "units": database.database.site.gui.units.default_discharge_units,
            }
        }
    elif measure_type in ["water_square", "total_storage", "greening"]:
        if not isinstance(value, list) and len(value) != 3:
            raise ValueError(f"Invalid value {value} for measure type {measure_type}")
        value_dict = {
            "volume": {
                "value": value[0],
                "units": database.database.site.gui.units.default_volume_units,
            },
            "height": {
                "value": value[1],
                "units": database.database.site.gui.units.default_length_units,
            },
            "percent_area": value[2],
        }
    elif measure_type in ["buyout_properties"]:
        if property_type not in ["residential", "commercial"]:
            raise ValueError(
                f"Invalid property type {property_type} for measure type {measure_type}"
            )
        value_dict = {"property_type": property_type}
    else:
        raise ValueError(f"Measure type {measure_type} not valid.")

    measure_dict = {"name": name, "selection_type": selection_type, **value_dict}
    if selection_type in ["polyline", "polygon"]:
        filepath = (
            database.database.input_path / "measures" / name / "selection.geojson"
        )
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            geojson.dump(geom, f)
        measure_dict["polygon_file"] = filepath.as_posix()
    if aggregation_area_type:
        measure_dict["aggregation_area_type"] = aggregation_area_type
    if aggregation_area_name:
        measure_dict["aggregation_area_name"] = aggregation_area_name

    return database.create_measure(type=measure_type, attrs=measure_dict)


def create_strategy(database: FloodAdapt, name: str, measure_list: list):
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
    if name not in strategies_existing["name"]:
        strategy_new = create_strategy_config(
            database=database, name=name, measure_list=measure_list
        )
        database.save_strategy(strategy_new)
        return strategy_new
    else:
        return database.get_strategy(name)


def create_strategy_config(database: FloodAdapt, name: str, measure_list: list):
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
    scenario_dict = {"name": name, "measures": measure_list}

    return database.create_strategy(attrs=scenario_dict)
