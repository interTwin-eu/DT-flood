import tomli
import os
from typing import Union
from pathlib import Path
import pandas as pd

from hydromt.data_catalog import DataCatalog

from flood_adapt.api import startup
from flood_adapt.api import events
from flood_adapt.api import projections
from flood_adapt.api import measures
from flood_adapt.api import strategies
from flood_adapt.api import scenarios
from flood_adapt.object_model.interface.database import IDatabase
from flood_adapt.object_model.interface.events import IEvent
from flood_adapt.object_model.interface.projections import IProjection
# from flood_adapt.object_model.interface.measures import IMeasure
from flood_adapt.object_model.interface.strategies import IStrategy
from flood_adapt.object_model.interface.scenarios import IScenario


def init_scenario(database_path: Union[str, os.PathLike], scenario_config_name: str) -> tuple[IDatabase, dict]:
    """Function fetching topmost objects for configuration

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

    if type(database_path) == str:
        database_path = Path(database_path)

    scenario_path = database_path / scenario_config_name

    db = startup.read_database(database_path=database_path.parent, site_name=database_path.stem)
    with open(scenario_path, 'rb') as f:
        scenario = tomli.load(f)

    return db, scenario

def create_scenario_config(database: IDatabase, scenario_config: dict) -> IScenario:
    scenario_dict = {
        'name': scenario_config['name'],
        'description': f"Scenario generated from toplevel {scenario_config['name']} config file",
        'event': scenario_config['event']['name'],
        'projection': scenario_config['projection']['name'],
        'strategy': scenario_config['strategy']['name'], 
    }
    return scenarios.create_scenario(attrs=scenario_dict, database=database)



def create_scenario(database: IDatabase, scenario_config: dict) -> IScenario:
    """Function to check if scenario already exists. If not, create it and save config file. If yes, return Scenario object of pre-existing event config

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
    scenarios_existing = scenarios.get_scenarios(database)

    # If necessary create new scenario, save it and return object, otherwise load existing and return object
    if not scenario_config['name'] in scenarios_existing['name']:
        scenario_new = create_scenario_config(database, scenario_config)
        scenarios.save_scenario(scenario_new, database)
        return scenario_new
    else:
        return scenarios.get_scenario(scenario_config['name'], database)


def create_event(database: IDatabase, scenario_config: dict) -> IEvent:
    """Function to check if event already exists. If not, create it and save config file. If yes, return Event object of pre-existing event config

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
    events_existing = events.get_events(database)
    # If necessary create new event, save it and return object, otherwise load existing and return object
    if not scenario_config["event"]["name"] in events_existing["name"]:
        event_new = create_event_config(database, scenario_config)
        events.save_event_toml(event_new, database)
        if event_new.attrs.tide.timeseries_file == 'placeholder.csv':
            with open(database.input_path/'events'/event_new.attrs.name/'placeholder.csv','w') as f:
                df = pd.DataFrame({'placeholder': [0]}, index=(['00:00:00']))
                df.to_csv(f)
        return event_new
    else:
        return events.get_event(scenario_config["event"]["name"], database)

def create_event_config(database: IDatabase, scenario_config: dict) -> IEvent:
    """Create FloodAdapt Event object from scenario configuration

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

    # Set event type
    if not database.site.attrs.sfincs.offshore_model:
        event_type = "Historical_nearshore"
    else: 
        # event_type = "offshore"
        raise NotImplementedError("Offshore models not (yet) supported here")
    
    # Set meteo forcing type
    dc = DataCatalog(scenario_config["event"]["data_catalogues"])
    if 'meteo' in scenario_config["event"]["sfincs_forcing"].keys():
        wind_type = 'none'
        rainfall_type = 'none'

    elif Path(scenario_config["event"]["sfincs_forcing"]["wind"]).suffix == ".nc":
        wind_type = 'none'
    elif Path(scenario_config["event"]["sfincs_forcing"]["rainfall"]).suffix == ".nc":
        rainfall_type = 'none'
    else:
        wind_type = 'timeseries'
        rainfall_type = 'timeseries'

    wind_dict = {'source': wind_type}
    if not wind_type == 'none':
        wind_dict['timeseries_file'] = scenario_config["event"]['sfincs_forcing']['wind']

    rainfall_dict = {'source': rainfall_type}
    if not rainfall_type == 'none':
        rainfall_dict['timeseries_file'] = scenario_config["event"]['sfincs_forcing']['rainfall']          

    
    # Set waterlevel forcing type
    tide_type = 'timeseries'
    tide_dict = {'source': tide_type}
    if (
        scenario_config["event"]["sfincs_forcing"]["waterlevel"] in dc.sources or 
        Path(scenario_config["event"]["sfincs_forcing"]["waterlevel"]).suffix == '.nc'
        ):
        placeholder_path = database.input_path/'events'/scenario_config["event"]["name"]/'placeholder.csv'
        tide_dict['timeseries_file'] = str(placeholder_path.name)
    else:
        tide_dict["timeseries_file"] = scenario_config["event"]["sfincs_forcing"]["waterlevel"]

    event_dict = {
        'name': scenario_config["event"]["name"],
        'description': f"Event generated from toplevel {scenario_config['name']} config file",
        'mode': 'single_event',
        'template': event_type,
        'timing': 'historical',
        'time': {
            'start_time': scenario_config["event"]["start_time"],
            'end_time': scenario_config["event"]["end_time"],
        },
        'river':  [{}],
        'tide': tide_dict,
        'wind': wind_dict,
        'rainfall': rainfall_dict,
        'surge': {'source': 'none'},
        'water_level_offset': {'value': 0, 'units': 'meters'}
    }

    return events.create_historical_nearshore_event(attrs = event_dict)


def create_projection(database: IDatabase, scenario_config: dict) -> IProjection:
    """Function to check if projection already exists. If not, create it and save config file. If yes, return Projection object of pre-existing projection config

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
    projections_existing = projections.get_projections(database)

    # If necessary create new projection, save it and return object, otherwise load existing and return object
    if not scenario_config["projection"]["name"] in projections_existing["name"]:
        projection_new = create_projection_config(database, scenario_config)
        projections.save_projection(projection_new, database)
        return projection_new
    else:
        return projections.get_projection(scenario_config["projection"]["name"], database)

def create_projection_config(database: IDatabase, scenario_config: dict) -> IProjection:
    """Create FloodAdapt Projection object from scenario configuration

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
        'name': scenario_config["projection"]["name"],
        'description': f"Projection generated from toplevel {scenario_config['name']} config file",
    }

    # Physical projection config
    phys_dict = {}
    for name in scenario_config["projection"]["physical_projection"]:
        if name == 'sea_level_rise' or name == 'subsidence':
            phys_dict.update({name: {'value': scenario_config["projection"]["physical_projection"][name], 'units': 'meters'}})
        else:
            phys_dict.update({name: scenario_config["projection"]["physical_projection"][name]})
    projection_dict.update({"physical_projection": phys_dict})

    # Socio-Economic config
    sec_dict = {}
    for name in scenario_config["projection"]["socio_economic_change"]:
        if name == 'new_development_elevation':
            sec_dict.update({name: {'value': scenario_config["projection"]["socio_economic_change"][name], 'units': 'meters'}})
        else:
            sec_dict.update({name: scenario_config["projection"]["socio_economic_change"][name]})
    projection_dict.update({'socio_economic_change': sec_dict})

    return projections.create_projection(attrs = projection_dict)


def create_strategy(database: IDatabase, scenario_config: dict) -> IStrategy:
    """Function to check if strategy already exists. If not, create it and save config file. If yes, return Strategy object of pre-existing strategy config

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
    strategies_existing = strategies.get_strategies(database)

    # If necessary create new strategy, save it and return object, otherwise load existing and return object
    if not scenario_config["strategy"]["name"] in strategies_existing['name']:
        strategy_new = create_strategy_config(database, scenario_config)
        strategies.save_strategy(strategy_new, database)
        return strategy_new
    else: return strategies.get_strategy(scenario_config["strategy"]["name"], database)

def create_strategy_config(database: IDatabase, scenario_config: dict) -> IStrategy:
    """Create FloodAdapt Strategy object from scenario configuration. Where necessary create new measures, otherwise use existing ones

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
        'name': scenario_config["strategy"]["name"],
        'description': f"Strategy generated from toplevel {scenario_config['name']} config file",
    }
    measure_list = []
    measures_existing = measures.get_measures(database)
    for measure in scenario_config["strategy"]:
        if not 'measure' in measure:
            continue

        measure_list.append(scenario_config['strategy'][measure]['name'])
        if not scenario_config['strategy'][measure]['name'] in measures_existing['name']:

            measure_dict = {}
            measure_dict.update({"name": scenario_config['strategy'][measure]['name'], "type": scenario_config['strategy'][measure]['type']})

            if Path(scenario_config['strategy'][measure]['selection']).exists():
                selection_type = 'polygon'
                polygon_file = scenario_config['strategy'][measure]['selection']
                measure_dict.update({'polygon_file': polygon_file})
            elif scenario_config['strategy'][measure]['selection'] == 'all':
                selection_type = 'all'
            else:
                selection_type = 'aggregation_area'

            measure_dict.update({'selection_type': selection_type})
            measure_dict.update(scenario_config['strategy'][measure]['misc'])
            measure_new = measures.create_measure(attrs=measure_dict, type=scenario_config['strategy'][measure]['type'], database=database)
            measures.save_measure(measure_new, database)

    scenario_dict.update({'measures': measure_list})
    return strategies.create_strategy(attrs=scenario_dict, database=database)

