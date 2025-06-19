"""Plot utility functions."""


import leafmap.leafmap as leafmap
from ipyleaflet import GeoData, GeomanDrawControl, LayersControl, LegendControl
from ipywidgets import Layout

from DT_flood.utils.plotting.sfincs import get_model_bounds


def _handle_draw(target, action, geo_json, geometry):
    # geometry.append([{action: geo_json}])
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

    layout = Layout(height="600px")

    m = leafmap.Map(center=center, zoom=10, scroll_wheel_zoom=True, layout=layout)

    return m


def draw_database_map(database, agg_area_name=None, **kwargs):
    """Draw interactive map at database location."""
    selected_geometry = []

    def handle_draw(target, action, geo_json):
        _handle_draw(
            target=target, action=action, geo_json=geo_json, geometry=selected_geometry
        )

    # def handle_click(event, feature, properties,):
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
