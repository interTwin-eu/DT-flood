"""RA2CE plotting utilities."""
import geopandas as gpd
import matplotlib as mpl
import numpy as np
from branca.colormap import StepColormap
from ipyleaflet import GeoJSON, LegendControl, WidgetControl
from ipywidgets import HTML, Button, HBox, Label, VBox
from matplotlib.colors import rgb2hex

from DT_flood.utils.plotting.map_utils import (
    add_plot_marker,
    legend_line,
    legend_marker,
    rm_layer_by_name,
)


def get_ra2ce_scenario_root(database, scenario):
    """Get RA2CE root dir of scenario."""
    database = database.database
    return database.scenarios.output_path.joinpath(scenario) / "Impacts" / "ra2ce"


def add_ra2ce_network(map, database, scenario):
    """Add RA2CE network layer to map."""
    cmap = mpl.colormaps["inferno_r"]
    vmin = 0.1
    N_clr = 3

    lgnd_vals = cmap(np.linspace(0, 1, N_clr))
    lgnd_keys = ["Lightly damaged", "Damaged", "Severly damaged"]
    lgnd = {lgnd_keys[i]: rgb2hex(lgnd_vals[i]) for i in range(N_clr)}

    ra2ce_root = get_ra2ce_scenario_root(database, scenario)
    base_graph = gpd.read_file(
        ra2ce_root / "static" / "output_graph" / "base_graph_edges.gpkg"
    )
    links = gpd.read_file(
        ra2ce_root
        / "static"
        / "output_graph"
        / "origins_destinations_graph_hazard_edges.gpkg"
    )

    if base_graph.crs != links.crs:
        links.crs = {"init": base_graph.crs}

    links["EV1_ma"] = links["EV1_ma"].replace({np.nan: 0})

    clr_list = [tuple(clr) for clr in cmap(np.linspace(0, 1, N_clr))]
    cmap = StepColormap(clr_list, vmin=vmin, vmax=links["EV1_ma"].max(), max_labels=3)

    msg = HTML()
    msg.value = "Click on road segment"

    def _set_style(feature):
        ev1_ma = feature["properties"]["EV1_ma"]
        is_bridge = True if feature["properties"]["bridge"] == "yes" else False
        clr = cmap(ev1_ma)
        return {
            "color": "gray" if ev1_ma < vmin or is_bridge else rgb2hex(clr),
            "fillColor": "gray" if ev1_ma < vmin or is_bridge else rgb2hex(clr),
            "opacity": 1,
            "weight": 2 if ev1_ma < vmin or is_bridge else 5,
        }

    def _create_popup(feature, **kwargs):
        rm_layer_by_name(map, "plot_line")
        ev1_ma = feature["properties"]["EV1_ma"]
        is_bridge = True if feature["properties"]["bridge"] == "yes" else False
        name = feature["properties"]["ref"]
        name += (
            f" {feature['properties']['name']}"
            if feature["properties"]["name"] != "nan"
            else ""
        )
        new_feature = feature
        new_feature["properties"]["style"]["weight"] = 12
        map.add(GeoJSON(data=new_feature, name="plot_line"))
        print(feature)
        msg.value = f"""
            <h4>Road: {name}</h4>
            <h4>Bridge: {is_bridge}</h4>
            <h4>Waterlevel: {ev1_ma:.2f}[m]</h4>
        """
        info_cntrl = _get_empty_box_roads(map)
        info_cntrl.widget.children += (msg,)

    geojson = GeoJSON(data=links.__geo_interface__, style_callback=_set_style, style={})
    legend = LegendControl(lgnd, position="bottomright", title="Damaged roads")

    map.add(geojson)
    geojson.on_click(_create_popup)
    map.add(legend)

    return map


def add_ra2ce_orig_dest(map, database, scenario):
    """Add RA2CE origin/destination points to map."""
    pop_scaling = 2000
    ra2ce_root = get_ra2ce_scenario_root(database, scenario)

    output_dir = ra2ce_root / "output" / "multi_link_origin_closest_destination"
    [origins] = output_dir.glob("*_origins.gpkg")
    origins = gpd.read_file(origins)
    [dest] = output_dir.glob("*_destinations.gpkg")
    dest = gpd.read_file(dest)

    [od_no_hazard] = output_dir.glob("*_optimal_routes_without_hazard.gpkg")
    od_no_hazard = gpd.read_file(od_no_hazard)
    [od_hazard] = output_dir.glob("*_optimal_routes_with_hazard.gpkg")
    od_hazard = gpd.read_file(od_hazard)

    def _set_style_origins(feature):
        size = feature["properties"]["POPULATION"] / pop_scaling
        return {"radius": size, "color": "black"}

    def _plot_routes(feature, **kwargs):
        rm_layer_by_name(map, "route_no_hazard")
        rm_layer_by_name(map, "route_hazard")
        rm_layer_by_name(map, "plot_marker")
        orig_id = feature["properties"]["o_id"]
        route_no_hazard = od_no_hazard[
            od_no_hazard["origin"] == orig_id
        ].drop_duplicates()
        route_hazard = od_hazard[od_hazard["origin"] == orig_id].drop_duplicates()

        plot_no_hazard = GeoJSON(
            data=route_no_hazard.__geo_interface__,
            style={"color": "green", "weight": 5},
            name="route_no_hazard",
        )
        plot_hazard = GeoJSON(
            data=route_hazard.__geo_interface__,
            style={"color": "red", "weight": 5},
            name="route_hazard",
        )

        # [dest_no_haz] = route_no_hazard["destination"].values
        # for _,row in dest[[id in dest_no_haz.split(",") for id in dest['d_id']]].iterrows():
        #     location = [row.geometry.y, row.geometry.x]
        #     print(f"Drawing no hazard dest marker at {location}")
        #     _add_plot_marker(map, location=location, color="green")
        # [dest_haz] = route_hazard["destination"].values
        # for _,row in dest[[id in dest_haz.split(",") for id in dest['d_id']]].iterrows():
        #     location = [row.geometry.y, row.geometry.x]
        #     print(f"Drawing hazard dest marker at {location}")
        #     _add_plot_marker(map, location=location, color="red")

        if not route_hazard["lengthDisr"].empty:
            [dist_diff] = (
                route_hazard["lengthDisr"].values - route_no_hazard["lengthNorm"].values
            )
            msg_str = f"Difference: {dist_diff/1000:.2f}[km]"
        else:
            msg_str = "No possible hazard route"
        msg = HTML()
        msg.value = f"""
            <b>{msg_str}</b>
        """
        info_cntrl = _get_empty_box_routes(map)
        info_cntrl.widget.children += (_routes_legend(), msg)

        add_plot_marker(map, location=feature["geometry"]["coordinates"][::-1])

        map.add(plot_no_hazard)
        map.add(plot_hazard)

    org_points = GeoJSON(
        data=origins.__geo_interface__,
        point_style={"weight": 2},
        style_callback=_set_style_origins,
    )
    org_points.on_click(_plot_routes)

    dest_points = GeoJSON(
        data=dest.__geo_interface__,
        point_style={"radius": 8, "color": "red", "weight": 2},
    )

    map.add(org_points)
    map.add(dest_points)

    return map


def button_rm_boxes(map):
    """Create button to remove RA2CE info boxes."""

    def _rm_boxes(button, **kwargs):
        box_titles = ["Road Info", "RA2CE Optimal Routes"]
        controls = [
            control for control in map.controls if isinstance(control, WidgetControl)
        ]
        for control in controls:
            if (
                isinstance(control.widget, VBox)
                and isinstance(control.widget.children[0], Label)
                and control.widget.children[0].value in box_titles
            ):
                map.remove(control)
        names = [layer.name for layer in map.layers]
        for name in names:
            if "plot_" in name:
                rm_layer_by_name(map, name)
        rm_layer_by_name(map, "route_no_hazard")
        rm_layer_by_name(map, "route_hazard")

    button = Button(
        description="Remove info boxes",
    )
    button.on_click(_rm_boxes)

    control = WidgetControl(widget=button, position="topleft")
    map.add(control)

    return map


def add_ra2ce_orig_dest_legend(map):
    """Add legend to map for origin/destination points."""
    canvas = legend_marker(color="black")
    orig_label = HBox([canvas, Label("Origin points")])

    canvas = legend_marker(color="red")
    dest_label = HBox([canvas, Label("Destination points")])

    title = Label("RA2CE Origin/Destination points")
    box = VBox([title, orig_label, dest_label])

    cntrl = WidgetControl(widget=box, position="bottomleft", transparent_bg=True)
    map.add(cntrl)
    return map


def _routes_legend():
    canvas = legend_line("green")
    no_haz_label = HBox([canvas, Label("Route no hazard")])

    canvas = legend_line("red")
    haz_label = HBox([canvas, Label("route hazard")])

    box = VBox([no_haz_label, haz_label])

    return box


def _get_empty_box_roads(map):
    controls = [
        control for control in map.controls if isinstance(control, WidgetControl)
    ]
    for control in controls:
        if (
            isinstance(control.widget, VBox)
            and isinstance(control.widget.children[0], Label)
            and control.widget.children[0].value == "Road Info"
        ):
            control.widget.children = [control.widget.children[0]]
            return control
    box = VBox([Label("Road Info")])
    cntrl = WidgetControl(widget=box, position="topright")
    map.add(cntrl)
    return cntrl


def _get_empty_box_routes(map):
    controls = [
        control for control in map.controls if isinstance(control, WidgetControl)
    ]
    for control in controls:
        if (
            isinstance(control.widget, VBox)
            and isinstance(control.widget.children[0], Label)
            and control.widget.children[0].value == "RA2CE Optimal Routes"
        ):
            control.widget.children = [control.widget.children[0]]
            return control
    box = VBox([Label("RA2CE Optimal Routes")])
    cntrl = WidgetControl(widget=box, position="topright")
    map.add(cntrl)
    return cntrl
