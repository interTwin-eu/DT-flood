

import solara
from ipyleaflet import Map, DrawControl, basemaps, TileLayer, LegendControl
from ipywidgets import Output
from IPython.display import display, HTML
import json
from pathlib import Path
import datetime as dt
import os
import tomli_w
import tomli

# from DT_flood.utils.workflow_utils import create_workflow_config, run_fa_scenario_workflow # , run_scenario

import logging
logging.getLogger('reacton').disabled = True

# for visualisation
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import ListedColormap, BoundaryNorm
from hydromt_fiat.fiat import FiatModel
import cartopy.crs as ccrs
import geopandas as gpd
matplotlib.use('Agg')

# FLOODMAP
from localtileserver import TileClient


proj = ccrs.PlateCarree()


from html2image import Html2Image



from flood_adapt.api.static import read_database
# from flood_adapt.config import Settings
from flood_adapt.api.scenarios import get_scenarios
from flood_adapt.api.strategies import get_strategies
from flood_adapt.api.measures import get_measures
from flood_adapt.api.projections import get_projections
from flood_adapt.api.events import get_events


########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################


###################################################### TO ADJUST #######################################################
name_overall = "scheveningen_nov24" # "scheveningen"
scenario = "DT-climate_baseline" # "test_scenario" # test_current_no_measures --> sucessful for metrics; test_scenario has no html
data_catalogues = [Path(r"/mnt/c/Users/santjer/OneDrive - Stichting Deltares/Documents/DestinE/Technical/01_FloodAdapt/deltares_data_wsl.yml")]

# db_path = Path(fr"C:\Users\santjer\OneDrive - Stichting Deltares\Documents\DestinE\Technical\01_FloodAdapt\{name_overall}_visualisation\{name_overall}")
db_path = Path(fr"C:\Users\santjer\OneDrive - Stichting Deltares\Documents\DestinE\Technical\01_FloodAdapt\{name_overall}")

hti = Html2Image('edge') # Specify preferred browser for metrics visualisation; 'chrome' and 'edge' are supported
########################################################################################################################

# fiat_path = db_path/"output"/"Scenarios"/scenario/"Impacts"/"fiat_model" 
fiat_path = db_path/"output"/"scenarios"/scenario/"Impacts"/"fiat_model" 
floodmap_path = db_path / "output" / "scenarios" / scenario / "Flooding" / f"FloodMap_{scenario}.tif"
fiat_output_path = fiat_path/"output"/"spatial.gpkg"
metrics_html_path = db_path /"output"/"scenarios"/scenario/f"{scenario}_metrics.html"

db = read_database(database_path = db_path.parent, site_name=db_path.stem)
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

##############################################################################################
######################################## DEMONSTRATOR ########################################
##############################################################################################

def handle_draw(target, action, geo_json):
    print(f"Action: {action}, GeoJSON: {geo_json}") 
    if action == 'created' and 'geometry' in geo_json:
        geo_type = geo_json['geometry']['type']
        coords = geo_json['geometry']['coordinates']
        
        if current_geometry_type.value and current_geometry_type.value != geo_type:
            error_message.value = f"**Error**: You cannot draw a {geo_type} after a {current_geometry_type.value}. Please clear the previous geometry before adding a new type."
            return
        
        if geo_type == 'Polygon':
            polygon_coords = coords[0]
            selected_geometry.value = {'type': 'Polygon', 'coordinates': polygon_coords}
            drawn_polygons.value.append({'type': 'Polygon', 'coordinates': polygon_coords})
            print("Polygon coordinates updated:", selected_geometry.value)
        
        elif geo_type == 'LineString':  # Handling polylines
            selected_geometry.value = {'type': 'LineString', 'coordinates': coords}
            drawn_polylines.value.append({'type': 'LineString', 'coordinates': coords})
            print("Polyline coordinates updated:", selected_geometry.value)

        elif geo_type == 'Point':  # Handling markers
            if point_placed.value:
                error_message.value = "**Error**: Only one point can be placed. Please first save the measure before adding another one."
                return
            selected_geometry.value = {'type': 'Point', 'coordinates': coords}
            drawn_markers.value.append({'type': 'Point', 'coordinates': coords})
            point_placed.set(True)  # Set point placed flag to True
            print("Marker coordinates updated:", selected_geometry.value)

        current_geometry_type.value = geo_type  # Update the current geometry type
        error_message.value = ""

def update_draw_tools_none():
    global draw_control
    m.remove_control(draw_control)
    new_draw_control = DrawControl(polyline={},polygon={},circlemarker={})
    draw_control = new_draw_control
    draw_control.on_draw(handle_draw)
    m.add_control(draw_control)

############################################## TAB EVENT ##############################################

def save_inputs(event_name, start_date, end_date):
    global event_dict
    event_dict["name"] = event_name
    event_dict["start_time"] = start_date.strftime('%Y-%m-%d %H:%M:%S')
    event_dict["end_time"] = end_date.strftime('%Y-%m-%d %H:%M:%S')
    event_dict["data_catalogues"] = ''
    event_dict["sfincs_forcing"] = {'meteo': '', 'waterlevel': ''}

############################################## TAB PROJECTIONS ##############################################

def save_inputs_projections():
        global proj_dict
        proj_dict["name"] = projName.value
        proj_dict["physical_projection"] = {'sea_level_rise': SLR_input.value,
                                            'rainfall_increase': RAIN_input.value}
        proj_dict["socio_economic_change"] = {'population_growth_existing': POP_input.value,
                                            'economic_growth': ECON_input.value}

############################################## TAB STRATEGY & MEASURES ##############################################

def clear_all_drawn_geometries():
    global draw_control
    m.remove_control(draw_control)
    draw_control = DrawControl(
        polyline={'shapeOptions': {'color': 'blue', 'weight': 4}},
        polygon={'shapeOptions': {'color': 'red', 'weight': 4}},
        marker={},
        rectangle={},
        circle={},    )
    draw_control.on_draw(handle_draw)
    m.add_control(draw_control)
    drawn_polylines.set([])
    drawn_polygons.set([])
    drawn_markers.set([])
    point_placed.set(False) 

def update_draw_tools():
    print(f"Updating draw tools for measure_type: {measure_type.value}")
    global draw_control
    m.remove_control(draw_control)
    
    if measure_type.value == "Floodwall":
        new_draw_control = DrawControl(polyline={'shapeOptions': {'color': 'blue', 'weight': 4}},polygon={},circlemarker={})
    elif measure_type.value == "Pump":
        new_draw_control = DrawControl(polyline={},polygon={},marker={})  # Enable marker only
    elif measure_type.value in ["Water square", "Green infrastructure", "Water storage", "Elevate properties", "Floodproof properties", "Buyout properties"]:
        new_draw_control = DrawControl(polyline={},polygon={'shapeOptions': {'color': 'red', 'weight': 4}},circlemarker={})

    draw_control = new_draw_control
    draw_control.on_draw(handle_draw)
    m.add_control(draw_control)

    drawn_polylines.set([])
    drawn_polygons.set([])
    drawn_markers.set([])
    point_placed.set(False)

def save_current_add_new():
        if selected_geometry.value is None:
            error_message.value = "**Error**: Please place the measure on the map."
            return
        else:
            error_message.set("")
        
        measure_misc  = {}
        if measure_type.value == "Floodwall":
            mtype = "floodwall"
            measure_misc = {"elevation": {"value": elevation_fw.value, "units": 'meters'}}
        elif measure_type.value == "Pump":
            mtype = "pump"
            measure_misc = {"discharge": {"value": discharge_fw.value, "units": 'm3/s'}}
        elif measure_type.value == "Water square":
            mtype = "water_square"
            measure_misc = {"volume": {"value": volume_ws.value, "units": 'm3'},
                            "height": {"value": height_ws.value, "units": "meters"}}
        elif measure_type.value == "Green infrastructure":
            mtype = "greening"
            measure_misc = {"volume": {"value": volume_gi.value, "units": 'm3'},
                            "height": {"value": height_gi.value, "units": "meters"},
                            "percent_area": percarea_gi.value}
        elif measure_type.value == "Water storage":
            mtype = "total_storage"
            measure_misc = {"volume": {"value": volume_wst.value, "units": 'm3'}}
        elif measure_type.value == "Elevate properties":
            mtype = "elevate_properties"
            measure_misc = {"elevation": {"value": elevation_prop.value, "units": 'meters'}}
        elif measure_type.value == "Floodproof properties":
            mtype = "floodproof_properties"
            measure_misc = {"elevation": {"value": elevation_fpprop.value, "units": 'meters'}}
        elif measure_type.value == "Buyout properties":
            mtype = "buyout_properties"
            measure_misc = {}

        measure = {
            "name": measureName.value,
            "type": mtype, # measure_type.value,
            "selection": selected_geometry.value,
            "misc": measure_misc        }
        measures_list.value.append(measure)
        save_directory = Path.cwd() # Path(r"/mnt/c/Users/santjer/OneDrive - Stichting Deltares/Documents/DestinE/Technical/02_Solara")
        geojson_data = {"measure_area": selected_geometry.value}
        geojson_filename = save_directory / f"{measureName.value}_geometry.geojson"
        with open(geojson_filename, 'w') as geojson_file:
            json.dump(geojson_data, geojson_file)
        measure["selection"] = str(geojson_filename) # - - - - - - - - - - - - - - - - - - - - - - - -
        clear_all_drawn_geometries()
        selected_geometry.set(None)
        current_geometry_type.set(None)
        measureName.set("Measure Name")
        measure_type.set("Floodwall")
        elevation_fw.set(0)
        discharge_fw.set(0) 
        volume_ws.set(0) 
        height_ws.set(0) 
        volume_gi.set(0) 
        height_gi.set(0) 
        percarea_gi.set(0)
        volume_wst.set(0) 
        elevation_prop.set(0) 
        elevation_fpprop.set(0)

def save_all_measures():
    global strategy
    error_message.set("")
    clear_all_drawn_geometries()
    selected_geometry.set(None)
    current_geometry_type.set(None)
    
    strategy = {'name': strategyName.value}
    for idx, measure in enumerate(measures_list.value, start=1):
        if measure['selection'] is None:
            continue
        measure_name = f"measure{idx}"
        file_path = Path.cwd() / f"{measure['name']}_geometry.geojson"# f"{measureName.value}_geometry.geojson" #####################
        strategy[measure_name] = {
            'name': measure['name'],
            'type': measure['type'].lower(), 
            'selection': str(file_path), # str(geojson_filename),
            'misc': measure['misc']}
    strategyName.set("Strategy Name")

def clear_measures():
    global strategy
    for measure in measures_list.value:
        measure_name = measure['name']
        file_path = Path.cwd() / f"{measure_name}_geometry.geojson"
        if file_path.exists():
            file_path.unlink()
    measures_list.set([]) 
    selected_geometry.set(None)
    current_geometry_type.set(None)
    error_message.set("")
    clear_all_drawn_geometries()
    measureName.set("Measure Name")
    measure_type.set("Floodwall")
    strategyName.set("Strategy Name")
    strategy = {} 

def save_strategy():
    save_current_add_new()
    save_all_measures()

############################################## TAB SCENARIO ##############################################
scenarioName = solara.reactive("Scenario Name")

try:
    if event_dict and 'name' in event_dict:
        all_events = [event_dict['name']] + get_events()["name"]
    else:
        all_events = get_events()["name"]
except NameError:
    all_events = get_events()["name"]
selected_event = solara.reactive(all_events[0])


try:
    if proj_dict and 'name' in proj_dict:
        all_projections = [proj_dict['name']] + get_projections()["name"] 
    else:
        all_projections = get_projections()["name"] 
except NameError:
    all_projections = get_projections()["name"]
selected_projection = solara.reactive(all_projections[0])


try:
    if strategy and 'name' in strategy:
        all_strategies = [strategy['name']] + get_strategies()["name"]
    else:
        all_strategies = get_strategies()["name"] 
except NameError:
    all_strategies = get_strategies()["name"] 
selected_strategy = solara.reactive(all_strategies[0])


def flatten_toml(toml_data_event, parent_key="", separator="."):
    flattened_dict = {}
    for key, value in toml_data_event.items():
        full_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            flattened_dict.update(flatten_toml(value, full_key, separator))
        else:
            flattened_dict[full_key] = value
    return flattened_dict

# EVENTS
def toml_to_event_dict(toml_path_event):
    with open(toml_path_event, "rb") as f:
        toml_data_event = tomli.load(f)
    flat_data = flatten_toml(toml_data_event)
    event_dict_select = {}
    for key, value in flat_data.items():
        parts = key.split(".")
        if len(parts) == 1:
            event_dict_select[parts[0]] = value
        else:
            current = event_dict_select
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
    return event_dict_select

def handle_event_selection(selected_event):
    global event_dict_select
    if selected_event.value in get_events()["name"]: # selected_event == event_dict['name']:
        toml_path_event = db_path / "input" / "events" / selected_event.value / f"{selected_event.value}.toml"
        event_dict_select = toml_to_event_dict(toml_path_event)
    else:
        event_dict_select = event_dict


# PROJECTIONS
def toml_to_proj_dict(toml_path_projection):
    with open(toml_path_projection, "rb") as f:
        toml_data_proj = tomli.load(f)
    flat_data = flatten_toml(toml_data_proj)
    proj_dict_select = {}
    for key, value in flat_data.items():
        parts = key.split(".")
        proj_dict_select[parts[0]] = value
    return proj_dict_select

def handle_projection_selection(selected_projection):
    global projection_dict_select
    if selected_projection.value in get_projections()["name"]: # == proj_dict['name']:
        toml_path_projection = db_path / "input" / "Projections" / selected_projection.value / f"{selected_projection.value}.toml"
        projection_dict_select = toml_to_proj_dict(toml_path_projection)
    else:
        projection_dict_select = proj_dict

        
# STRATEGIES
def toml_to_strategy_dict(toml_path_strategy):
    with open(toml_path_strategy, "rb") as f:
        toml_data_strategy = tomli.load(f)
    flat_data = flatten_toml(toml_data_strategy)
    strategy_dict_select = {}
    for key, value in flat_data.items():
        parts = key.split(".")
        strategy_dict_select[parts[0]] = value
    return strategy_dict_select

def handle_strategy_selection(selected_strategy):
    global strategy_dict_select
    if selected_strategy.value in get_strategies()["name"]:# == strategy['name']:
        toml_path_strategy = db_path / "input" / "Strategies" / selected_strategy.value / f"{selected_strategy.value}.toml"
        strategy_dict_select = toml_to_strategy_dict(toml_path_strategy)
    else:
        strategy_dict_select = strategy

# SCENARIO
def initialise_scenario(selected_event, selected_projection, selected_strategy):
    handle_event_selection(selected_event)
    handle_projection_selection(selected_projection)
    handle_strategy_selection(selected_strategy)
    global scenario
    scenario = {
        'name': scenarioName.value, # "test_scenario",
        'event': event_dict_select, # selected_event.value, # event_dict,
        'projection': projection_dict_select, # proj_dict,
        'strategy': strategy_dict_select, # strategy,
    }

############################################## TAB SAVE ##############################################
def save():
    scenario_fn = db_path / f"{scenario['name']}_toplevel.toml" # fa_database
    with open(scenario_fn, 'wb+') as f:
            tomli_w.dump(scenario, f)


############################################## TAB RUN ##############################################
def run():
    scenario_name = scenarioName.value
    create_workflow_config(database_fn, scenario_name)     # NOT SUCCESSFUL!!! ###############################################################
    run_fa_scenario_workflow(database_fn, scenario_name)   # NOT SUCCESSFUL!!! ###############################################################

############################################## TAB VISUALISATION  ##############################################

def on_checkbox_change(checkbox_id):
    if checkbox_id == 1:
        mapchoice1.set(True)
        mapchoice2.set(False)
        mapchoice3.set(False)
        mapchoice4.set(False)
        selected_view.set("map1")
    elif checkbox_id == 2:
        mapchoice1.set(False)
        mapchoice2.set(True)
        mapchoice3.set(False)
        mapchoice4.set(False)
        selected_view.set("map2")
    elif checkbox_id == 3:
        mapchoice1.set(False)
        mapchoice2.set(False)
        mapchoice3.set(True)
        mapchoice4.set(False)
        selected_view.set("map3")
    elif checkbox_id == 4:
        mapchoice1.set(False)
        mapchoice2.set(False)
        mapchoice3.set(False)
        mapchoice4.set(True)
        selected_view.set("map4")
    else:
        mapchoice1.set(False)
        mapchoice2.set(False)
        mapchoice3.set(False)
        mapchoice4.set(False)
        selected_view.set(None)
        

def map1():
    if os.path.exists("temp_floodmap.tiff"):
        os.remove("temp_floodmap.tiff")
    vmin = 0; vmax = 3
    floodmap = xr.open_dataarray(floodmap_path).rio.reproject(4326)
    floodmap_clipped = floodmap.clip(min=vmin, max=vmax)
    mask = (floodmap_clipped <= 0) | np.isnan(floodmap_clipped)
    cmap = plt.get_cmap('Blues')
    colors = cmap(np.linspace(0, 1, cmap.N))
    colors[:, -1] = 1  
    colors[0, -1] = 0  
    custom_cmap = ListedColormap(colors)
    bounds = np.linspace(vmin, vmax, (vmax - vmin) + 1)
    norm = BoundaryNorm(bounds, custom_cmap.N)
    floodmap_clipped.rio.set_nodata(np.nan)
    floodmap_clipped.rio.to_raster("temp_floodmap.tiff", dtype='float32')
    tile_client = TileClient("temp_floodmap.tiff")
    m = Map(center=(52.1, 4.3), zoom=10, basemap=basemaps.OpenStreetMap.Mapnik)
    tile_layer = TileLayer(url=tile_client.get_tile_url(), opacity=1.0)
    m.add_layer(tile_layer)
    colors_legend = {"0 m": "#000000","1 m": "#555555","2 m": "#AAAAAA","≥3 m": "#FFFFFF"}
    legend = LegendControl(
        colors_legend,
        name="Flood Levels",
        position="bottomleft",
    )
    m.add_control(legend)
    floodmap.close()
    del tile_client
    plt.close()
    display(m)

def map2():
    fiat = FiatModel(root=fiat_path, mode='r')
    fiat.read()
    gdf_fiat = fiat.exposure.get_full_gdf(fiat.exposure.exposure_db)
    fiat_output = gpd.read_file(fiat_output_path).to_crs("EPSG:4326")
    fiat_output["Total Damage Normalized"] = fiat_output['Total Damage']/(gdf_fiat["Max Potential Damage: Structure"]+gdf_fiat["Max Potential Damage: Content"])
    fiat_output["Inundation Depth"].dropna() # fiat_output["Inundation Depth"].dropna().plot()
    ##################### PLOT #####################
    m = fiat_output.explore(column="Total Damage Normalized")
    display(m)

def map3():
    with open(metrics_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    display(HTML(html_content))

def map4():
    with open(metrics_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    hti.screenshot(html_str=html_content, save_as="metrics_image.png")   
    solara.Image("metrics_image.png")


########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

polyline_coordinates = solara.reactive([])
polygon_coordinates = solara.reactive([])
marker_coordinates = solara.reactive([])
drawn_polylines = solara.reactive([])
drawn_polygons = solara.reactive([])
drawn_markers = solara.reactive([])
selected_geometry = solara.reactive(None) 
selected_tab = solara.reactive('Event') 
measures_list = solara.reactive([])
error_message = solara.reactive("")
current_geometry_type = solara.reactive(None)
point_placed = solara.reactive(False)
open_delete_confirmation = solara.reactive(False)

m = Map(center=(52.08654741528378, 4.295223531699989), zoom=10, scroll_wheel_zoom=True, basemap=basemaps.OpenStreetMap.Mapnik)

draw_control = DrawControl(
    polyline={'shapeOptions': {'color': 'blue', 'weight': 4}},
    polygon={'shapeOptions': {'color': 'red', 'weight': 4}},
    marker={},
    rectangle={},  
    circle={},
)

draw_control.on_draw(handle_draw)
m.add_control(draw_control)

map_output = Output()
with map_output:
    display(m)

####################################### TAB WEATHER EVENT #######################################
event_dict = {}

@solara.component
def TabEvent():
    update_draw_tools_none()
    start_date = solara.use_reactive(dt.date.today())
    end_date = solara.use_reactive(dt.date.today())
    eventName = solara.use_reactive("Event Name")
    
    with solara.Card("Configure the Weather Event", style={"width": "100%", "padding": "10px"}):
        solara.InputText("Event Name", value=eventName, continuous_update=True)
        solara.Markdown(f"**Your Event Name**: {eventName.value}")

        solara.Text("Select the Start Date:")
        solara.lab.InputDate(start_date)
        
        solara.Text("Select the End Date:")
        solara.lab.InputDate(end_date)
        
        if end_date.value < start_date.value:
            solara.Markdown("**Warning**: The end date cannot be earlier than the start date.", style={"color": "red"})
        
        solara.Button("Save Inputs", on_click=lambda: save_inputs(eventName.value, start_date.value, end_date.value))


####################################### TAB PROJECTIONS #######################################
SLR_input = solara.reactive(0.0)
RAIN_input = solara.reactive(0.0)
POP_input = solara.reactive(0.0)
ECON_input = solara.reactive(0.0)
projName = solara.reactive("Projection Name")
proj_dict = {}

@solara.component
def TabProjections():
    update_draw_tools_none()

    with solara.Card("Projections", style={"width": "100%", "padding": "10px"}):
        solara.InputText("Projection Name", value=projName, continuous_update=True)
        solara.Markdown(f"**Your Projection Name**: {projName.value}")
        solara.InputFloat("Sea Level Rise (metres)", value=SLR_input, continuous_update=True)
        solara.InputFloat("Precipitation Increase (%)", value=RAIN_input, continuous_update=True)
        solara.InputFloat("Population Growth (%)", value=POP_input, continuous_update=True)
        solara.InputFloat("Economic Growth (%)", value=ECON_input, continuous_update=True)
        
        solara.Button("Save Inputs", on_click=save_inputs_projections, style={"margin-top": "20px"})

####################################### TAB MEASURES/STRATEGY #######################################
strategyName = solara.reactive("Strategy Name")
measureName = solara.reactive("Measure Name")
measure_types = ["Floodwall","Pump","Water square","Green infrastructure","Water storage",
                 "Elevate properties","Floodproof properties","Buyout properties"]
measure_type = solara.reactive("Floodwall")
elevation_fw = solara.reactive(0)  # For floodwall 
discharge_fw = solara.reactive(0)  # For pump 
volume_ws = solara.reactive(0)  # For water square
height_ws = solara.reactive(0)  # For water square 
volume_gi = solara.reactive(0)  # For green infrastructure
height_gi = solara.reactive(0)  # For green infrastructure
percarea_gi = solara.reactive(0)  # For green infrastructure 
volume_wst = solara.reactive(0)  # For water storage 
elevation_prop = solara.reactive(0)  # For properties 
elevation_fpprop = solara.reactive(0)  # For floodproof properties 
strategy = {} 

@solara.component
def TabStrategy(): 
    with solara.Card("Strategy Name", style={"width": "100%", "padding": "10px"}):
        solara.InputText("Strategy Name", value=strategyName, continuous_update=True)
        
    with solara.Card("Measures", style={"width": "100%", "padding": "10px"}):
        solara.InputText("Measure Name", value=measureName, continuous_update=True)
        solara.Markdown(f"**Your Measure Name**: {measureName.value}")
        
        duplicate_found = any(measure["name"] == measureName.value for measure in measures_list.value) 
        if duplicate_found:
            solara.Markdown(f"**Error**: A measure with the name '{measureName.value}' already exists. Please choose a different name.", style={"color": "red"})
        
        solara.Select(label="Measure Type", value=measure_type, values=measure_types)

        if measure_type.value == "Floodwall":
            solara.InputFloat("Elevation [m]", value=elevation_fw, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Pump":
            solara.InputFloat("Discharge [m³/s]", value=discharge_fw, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Water square":
            solara.InputFloat("Volume [m³]", value=volume_ws, continuous_update=True)
            solara.InputFloat("Height [m]", value=height_ws, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Green infrastructure":
            solara.InputFloat("Volume [m³]", value=volume_gi, continuous_update=True)
            solara.InputFloat("Height [m]", value=height_gi, continuous_update=True)
            solara.InputFloat("Percentage of area [%]", value=percarea_gi, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Water storage":
            solara.InputFloat("Volume [m³]", value=volume_wst, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Elevate properties":
            solara.InputFloat("Elevation [m]", value=elevation_prop, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Floodproof properties":
            solara.InputFloat("Elevation [m]", value=elevation_fpprop, continuous_update=True)
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])
        elif measure_type.value == "Buyout properties":
            solara.use_effect(lambda: update_draw_tools(), [measure_type.value])

        solara.Markdown("Click on the map to place the measure location (or draw a shape).")
        if measures_list.value:
            selected_measures = [f"{measure['type']}, '{measure['name']}'" for measure in measures_list.value]
            formatted_measures = "\n".join(selected_measures)
            solara.Markdown(f"**Selected Measures:**\n{formatted_measures}")

        if error_message.value:
            solara.Markdown(error_message.value, style={"color": "red"})

        with solara.Row():
            solara.Button("Save Current and Add New Measure", on_click=save_current_add_new, style={"margin-top": "20px", "margin-left": "-20px"})
            solara.Button("Clear All", on_click=clear_measures, style={"margin-top": "80px", "margin-left": "-348px"})
            solara.Button("Save Strategy", on_click=save_strategy, style={"margin-top": "80px", "margin-left": "54px"})

####################################### TAB SCENARIO #######################################
scenarioName = solara.reactive("Scenario Name")
@solara.component
def TabScenario():
    update_draw_tools_none() 

    with solara.Card("Initialise Scenario", style={"width": "100%", "padding": "10px"}):
        solara.InputText("Scenario Name", value=scenarioName, continuous_update=True)
        solara.Markdown(f"**Your Scenario Name**: {scenarioName.value}")
        with solara.Row(gap="10px"):
            solara.Select(label="Select Event", value=selected_event, values=all_events)
        with solara.Row(gap="10px"):
            solara.Select(label="Select Projection", value=selected_projection, values=all_projections)
        with solara.Row(gap="10px"):
            solara.Select(label="Select Strategy", value=selected_strategy, values=all_strategies)
        solara.Button("Initialise Scenario", on_click=lambda: initialise_scenario(selected_event, selected_projection, selected_strategy)) 


####################################### TAB SAVE #######################################
@solara.component
def TabSave():
    update_draw_tools_none() 

    with solara.Card("Save inputs and Run model", style={"width": "100%", "padding": "10px"}):
        # solara.InputText("Scenario Name", value=scenarioName, continuous_update=True)
        solara.Markdown(f"**Your Scenario Name**: {scenarioName.value}")
        solara.Button("Save", on_click=lambda: save()) 

####################################### TAB RUN #######################################
@solara.component
def TabRun():
    update_draw_tools_none() 

    with solara.Card("Save inputs and Run model", style={"width": "100%", "padding": "10px"}):
        solara.Markdown("**Run Scenario:**")
        solara.Button("Run", on_click=lambda: run()) 


####################################### TAB VISUALISATION #######################################
mapchoice1 = solara.reactive(False)
mapchoice2 = solara.reactive(False)
mapchoice3 = solara.reactive(False)
mapchoice4 = solara.reactive(False)
selected_view = solara.reactive(None)  

@solara.component
def TabVisualisation():
    update_draw_tools_none()
    with solara.Card("Map Visualisation", style={"width": "100%", "padding": "10px"}):
        solara.Markdown(f"<span style='color: #4682B4;'><b>Please Note:</b> The  generation of figures may take some seconds.</span>")
        solara.Markdown(f"If Metrics do not show, select the static option.")
        solara.Markdown(f"**Selection**:")
        solara.Checkbox(label="Floodmap", value=mapchoice1, on_value=lambda v: on_checkbox_change(1) if v else None)
        solara.Checkbox(label="Building Damages", value=mapchoice2, on_value=lambda v: on_checkbox_change(2) if v else None)
        solara.Checkbox(label="Metrics", value=mapchoice3, on_value=lambda v: on_checkbox_change(3) if v else None)
        if mapchoice3.value:
            with solara.Div(style={"margin-left": "20px"}): 
                solara.Checkbox(label="Metrics (static)", value=mapchoice4, on_value=lambda v: on_checkbox_change(4) if v else None)

###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
###########################################################################################
@solara.component
def SettingsTabs():
    with solara.Column(style={"width": "100%", "align-items": "center"}):
        with solara.Row(gap="10px", style={"justify-content": "flex-start", "width": "80%"}):
            solara.Button("Event", on_click=lambda: (selected_tab.set('Event'), selected_view.set(None)))
            solara.Button("Projections", on_click=lambda: (selected_tab.set('Projections'), selected_view.set(None)))
            solara.Button("Strategy", on_click=lambda: (selected_tab.set('Strategy'), selected_view.set(None)))
        with solara.Row(gap="10px", style={"justify-content": "flex-start", "width": "80%"}):
            solara.Button("Scenario", on_click=lambda: (selected_tab.set('Scenario'), selected_view.set(None)))
            solara.Button("Save", on_click=lambda: (selected_tab.set('Save'), selected_view.set(None)))
            solara.Button("Run", on_click=lambda: (selected_tab.set('Run'), selected_view.set(None)))
        with solara.Row(gap="10px", style={"justify-content": "flex-start", "width": "80%"}):
            solara.Button("Visualisation", on_click=lambda: selected_tab.set('Visualisation'))
 
    if selected_tab.value == 'Event':
        TabEvent()
    elif selected_tab.value == 'Projections':
        TabProjections()
    elif selected_tab.value == 'Strategy':
        TabStrategy()
    elif selected_tab.value == 'Scenario':
        TabScenario()
    elif selected_tab.value == 'Save':
        TabSave()
    elif selected_tab.value == 'Run':
        TabRun()
    elif selected_tab.value == 'Visualisation':
        TabVisualisation()
        mapchoice1.set(False); mapchoice2.set(False); mapchoice3.set(False)

@solara.component
def Page():
    with solara.Columns():
        with solara.Column(style={"width": "70%", "min-width": "650px"}):
            if selected_view.value == "map1":
                map1()
            elif selected_view.value == "map2":
                map2()
            elif selected_view.value == "map3":
                map3()
            elif selected_view.value == "map4":
                map4()
            else:
                display(m) 

        with solara.Column(style={"width": "30%", "min-width": "500px"}):
            SettingsTabs()

Page()

