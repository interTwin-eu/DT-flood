"""Plot utility functions."""
import leafmap.leafmap as leafmap
import matplotlib as mpl
import numpy as np
import xarray as xr
from ipyleaflet import (
    ColormapControl,
    DrawControl,
    GeoData,
    GeomanDrawControl,
    LayersControl,
    LegendControl,
    WidgetControl,
)
from ipywidgets import Button, Image, Layout, ToggleButtons

from DT_flood.utils.plotting.fiat import add_fiat_impact, list_agg_areas
from DT_flood.utils.plotting.map_utils import get_layer_by_name, rm_layer_by_name
from DT_flood.utils.plotting.ra2ce import (
    add_ra2ce_network,
    add_ra2ce_orig_dest,
    add_ra2ce_orig_dest_legend,
    button_rm_boxes,
)
from DT_flood.utils.plotting.sfincs import (
    add_sfincs_bzs_points,
    add_sfincs_dep_map,
    add_sfincs_dis_points,
    add_sfincs_legend,
    add_sfincs_riv_map,
    get_model_bounds,
    get_sfincs_scenario_model,
)
from DT_flood.utils.plotting.wflow import (
    add_wflow_elev_map,
    add_wflow_gauges_map,
    add_wflow_geoms_map,
    get_wflow_scenario_model,
)


def _handle_draw(target, action, geo_json, geometry):
    if action != "remove":
        geometry.append(geo_json[0]["geometry"])
        for item in reversed(geometry):
            if item != geo_json[0]["geometry"]:
                geometry.pop(geometry.index(item))
    else:
        for item in reversed(geometry):
            geometry.pop(geometry.index(item))
        target.clear()

    return geometry


def _handle_click(geometry, agg_area_name, **kwargs):
    for item in reversed(geometry):
        geometry.pop(geometry.index(item))
    geometry.append(
        {"agg_type": agg_area_name, "area_name": kwargs["properties"]["name"]}
    )
    return geometry


def create_base_map(database):
    """Create base map layer in database region."""
    [center] = database.get_model_boundary().dissolve().centroid.to_crs(4326)
    center = [center.y, center.x]

    layout = Layout(height="1200px")

    m = leafmap.Map(center=center, zoom=10, scroll_wheel_zoom=True, layout=layout)

    for control in m.controls:
        if isinstance(control, DrawControl):
            m.remove(control)

    return m


def draw_database_map(database, agg_area_name=None, **kwargs):
    """Draw interactive map at database location."""
    selected_geometry = []

    def handle_draw(target, action, geo_json):
        _handle_draw(
            target=target, action=action, geo_json=geo_json, geometry=selected_geometry
        )

    def handle_click(**kwargs):
        _handle_click(geometry=selected_geometry, agg_area_name=agg_area_name, **kwargs)

    if agg_area_name is not None:
        agg_area = database.get_aggregation_areas()[agg_area_name]

    m = create_base_map(database=database)

    geodata = GeoData(
        geo_dataframe=get_model_bounds(database),
        style={"color": "black", "fillOpacity": 0, "dashArray": "8"},
        name="SFINCS model boundary",
    )

    m.add(geodata)

    agg_area_layer = GeoData(
        geo_dataframe=agg_area,
        style={"color": "#3366cc", "fillColor": "#3366cc", "fillOpacity": 0.1},
        hover_style={"fillColor": "#3366cc", "fillOpacity": 0.5},
        name=f"Aggregation areas {agg_area_name}",
    )
    agg_area_layer.on_click(handle_click)
    m.add(agg_area_layer)

    m.add(LayersControl())

    draw_control = GeomanDrawControl()
    draw_control.on_draw(handle_draw)
    m.add(draw_control)

    legend = LegendControl({"SFINCS boundary": "black"}, title="Legend")
    if agg_area_name:
        legend.add_legend_element(f"{agg_area_name}", "#3366cc")
    legend.position = "bottomright"

    m.add(legend)

    return m, selected_geometry


def draw_scenario_sfincs(database, scenario, layer="dep"):
    """Plot the SFINCS output maps for a scenario."""
    if layer not in ["dep", "floodmap"]:
        raise ValueError("Select valid SFINCS map data layer")

    map = create_base_map(database)
    map.add(LayersControl(position="topleft"))
    map = button_rm_plots(map)

    sf = get_sfincs_scenario_model(database, scenario)

    map = add_sfincs_riv_map(map, sf)
    map = add_sfincs_dis_points(map, sf)
    map = add_sfincs_bzs_points(map, sf)

    map = add_sfincs_legend(map)

    if layer == "floodmap":
        map = add_floodmap(map, database, scenario)
    if layer == "dep":
        map = add_sfincs_dep_map(map, sf)

    del sf

    return map


def draw_scenario_fiat(database, scenario, agg_layer):
    """Plot the FIAT output maps for a scenario."""
    valid_aggs = ["building_footprints", *list_agg_areas(database)]
    if agg_layer not in valid_aggs:
        raise ValueError(f"{agg_layer} not among valid options {valid_aggs}")

    map = create_base_map(database)
    map.add(LayersControl(position="topleft"))

    map = add_floodmap(map, database, scenario)
    map = add_fiat_impact(map, database, scenario, agg_layer)

    return map


def draw_scenario_ra2ce(database, scenario):
    """Plot RA2CE output map for a scenario."""
    map = create_base_map(database)
    map = add_floodmap(map, database, scenario)

    map = add_ra2ce_network(map, database, scenario)
    map = add_ra2ce_orig_dest(map, database, scenario)
    map = add_ra2ce_orig_dest_legend(map)
    map = button_rm_boxes(map)
    return map


def draw_scenario_wflow(database, scenario):
    """Plot WFLOW maps for a scenario."""
    map = create_base_map(database)

    toggle = ToggleButtons(options=["Warmup", "Event"])

    cntrl = WidgetControl(widget=toggle, position="topright")
    map.add(cntrl)

    def _update_map(map, mode):
        wf = get_wflow_scenario_model(database, scenario, mode=mode.lower())

        for layer in map.layers:
            if "wflow" in layer.name:
                map.remove(layer)
        for control in map.controls:
            if isinstance(control, ColormapControl):
                map.remove(control)
            elif isinstance(control, WidgetControl) and isinstance(
                control.widget, Image
            ):
                map.remove(control)
        rm_layer_by_name(map, "plot_marker")

        map = add_wflow_elev_map(map, wf)
        map = add_wflow_geoms_map(map, wf)
        map = add_wflow_gauges_map(map, wf)

    def _update_func(func, map):
        def _new_func(change):
            return func(map, change["new"])

        return _new_func

    redraw_func = _update_func(_update_map, map)
    toggle.observe(redraw_func, "value")

    return map


def add_floodmap(map, database, scenario):
    """Add Floodmap layer to map."""
    database = database.database
    flood_fn = (
        database.scenarios.output_path.joinpath(scenario)
        / "Flooding"
        / f"FloodMap_{scenario}.tif"
    )
    base_fn = database.static_path / "dem" / "dep_subgrid.tif"

    flood = xr.open_dataarray(flood_fn)
    base = xr.open_dataarray(base_fn)

    base = base.sel(band=1)
    flood = flood.sel(band=1)
    base = base.interp_like(flood)
    flood = flood.where(base >= 0, np.nan)

    base.close()
    del base

    vmin = 0
    vmax = 2
    N = 5
    bins = [*np.linspace(vmin, vmax, N), np.inf]

    flood_grp = flood.groupby_bins(flood, bins)
    flood_bin = flood_grp.map(lambda x: x - x + x.min(), shortcut=False)
    flood_bin = flood_bin.sortby([flood_bin.x]).interp_like(flood, method="nearest")

    flood.close()
    del flood

    cmap = mpl.colormaps["Blues"]
    legend_keys = [f"<={i}" for i in bins[1:-1]]
    legend_keys.append(f">{bins[-2]}")
    legend_vals = cmap(np.linspace(0, 1, N))
    lgnd = {legend_keys[i]: mpl.colors.rgb2hex(legend_vals[i]) for i in range(N)}

    map.add_raster(
        flood_bin,
        vmin=vmin,
        vmax=vmax,
        nodata=np.nan,
        colormap=cmap,
        layer_name="Floodmap",
    )
    lgnd_control = LegendControl(lgnd, title="Flood Depth [m]", position="bottomleft")
    floodmap_layer = get_layer_by_name(map, "Floodmap")
    floodmap_layer.subitems = floodmap_layer.subitems + (lgnd_control,)

    return map


def button_rm_plots(map):
    """Add button to map to remove plot box."""

    def _rm_plot(button, **kwargs):
        controls = [
            control for control in map.controls if isinstance(control, WidgetControl)
        ]
        for control in controls:
            if isinstance(control.widget, Image):
                map.remove(control)

        names = [layer.name for layer in map.layers]
        for name in names:
            if "plot_" in name:
                rm_layer_by_name(map, name)

    button = Button(
        description="Remove plot box",
    )
    button.on_click(_rm_plot)

    control = WidgetControl(widget=button, position="topleft")
    map.add(control)

    return map
