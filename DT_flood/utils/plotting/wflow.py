"""WFLOW plotting utilities."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from branca.colormap import LinearColormap
from hydromt_wflow import WflowModel
from ipyleaflet import ColormapControl, GeoJSON
from matplotlib import colors

from DT_flood.utils.plotting.map_utils import (
    add_fig_to_widg,
    add_plot_box,
    add_plot_marker,
    rm_layer_by_name,
)
from DT_flood.utils.plotting.sfincs_styling import (
    geodata_dis_style,
    geodata_dis_style_point,
)


def get_wflow_scenario_model(database, scenario, mode="event"):
    """Get wflow model for scenario."""
    if mode not in ["event", "warmup"]:
        raise ValueError(f"Model wflow_{mode} is not a valid wflow model.")
    database = database.database
    wf_path = (
        database.scenarios.output_path.joinpath(scenario) / "Flooding" / f"wflow_{mode}"
    )
    wf = WflowModel(root=wf_path, mode="r+")
    wf.read()
    wf.read_staticmaps("staticmaps.nc")
    return wf


def add_wflow_elev_map(map, wf):
    """Add WFLOW elevation layer to map."""
    dem = wf.staticmaps["wflow_dem"].raster.mask_nodata()

    vmin, vmax = dem.quantile([0.0, 0.98]).round(1).values
    c_dem = plt.cm.terrain(np.linspace(0.25, 1, 256))
    cmap = colors.LinearSegmentedColormap.from_list("dem", c_dem)

    map.add_raster(
        dem, vmin=vmin, vmax=vmax, colormap=cmap, nodata=np.nan, layer_name="wflow_elev"
    )

    cmap = LinearColormap(colors=[tuple(c) for c in c_dem], vmin=vmin, vmax=vmax)
    cntrl = ColormapControl(
        colormap=cmap,
        value_min=vmin,
        value_max=vmax,
        caption="Elevation [m]",
        position="bottomleft",
        transparent_bg=True,
    )
    map.add(cntrl)

    return map


def add_wflow_geoms_map(map, wf):
    """Add WFLOW geoms to map."""
    gdf_bas = wf.basins
    gdf_riv = wf.rivers

    def _set_style_riv(feature):
        return {
            "color": "blue",
            "fillColor": "blue",
            "opacity": "1",
            "weight": feature["properties"]["strord"] / 2,
        }

    riv_layer = GeoJSON(
        data=gdf_riv.__geo_interface__,
        style={},
        style_callback=_set_style_riv,
        name="wflow_river",
    )
    bas_layer = GeoJSON(
        data=gdf_bas.unary_union.boundary.__geo_interface__,
        style={"color": "gray", "weight": 2},
        name="wflow_boundary",
    )

    map.add(riv_layer)
    map.add(bas_layer)

    if "reservoirs" in wf.geoms:
        res_layer = GeoJSON(
            data=wf.geoms["reservoirs"].__geo_interface__,
            style={
                "color": "black",
                "fillColor": "lightblue",
                "weight": 1,
                "opacity": 1,
                "fillOpacity": 1,
            },
            name="wflow_reservoir",
        )
        map.add(res_layer)

    return map


def add_wflow_gauges_map(map, wf):
    """Add WFLOW gauges layer to map."""
    gauges = wf.geoms["gauges"]
    gauges_src = wf.geoms["gauges_src"]

    gauges_layer = GeoJSON(
        data=gauges.__geo_interface__,
        style={
            "color": "black",
            "radius": 8,
            "opacity": 0.5,
            "weigth": 2,
            "dashArray": 2,
            "fillOpacity": 0.6,
            "fillColor": "blue",
        },
        point_style={
            "radius": 5,
            "color": "red",
            "fillOpacity": 0.8,
            "weight": 3,
            "fillColor": "blue",
        },
        name="wflow_downstream",
    )
    gauges_src_layer = GeoJSON(
        data=gauges_src.__geo_interface__,
        name="wflow_gauges",
        style=geodata_dis_style,
        point_style=geodata_dis_style_point,
    )

    map.add(gauges_src_layer)
    map.add(gauges_layer)

    def _update_plot_src(feature, **kwargs):
        index = feature["properties"]["index"]
        fig = plt.figure()
        ax = fig.add_subplot()
        wf.results["Q_gauges_src"].sel(index=index).plot(ax=ax)
        ax.set_ylabel("Discharge [m^3/s]")
        ax.set_title(f"SFINCS boundary point {index}")
        plt.grid()

        rm_layer_by_name(map, "plot_marker")
        im_wdg = add_plot_box(map)

        add_fig_to_widg(im_widg=im_wdg, fig=fig)
        add_plot_marker(map, location=feature["geometry"]["coordinates"][::-1])

    def _update_plot(feature, **kwargs):
        index = feature["properties"]["fid"]
        fig = plt.figure()
        ax = fig.add_subplot()
        wf.results["Q_gauges"].sel(index=index).plot(ax=ax)
        ax.set_ylabel("Discharge [$m^3$/s]")
        ax.set_title(f"Downstream point ID {index}")
        plt.grid()

        rm_layer_by_name(map, "plot_marker")
        im_wdg = add_plot_box(map)

        add_fig_to_widg(im_widg=im_wdg, fig=fig)
        add_plot_marker(map, location=feature["geometry"]["coordinates"][::-1])

    gauges_src_layer.on_click(_update_plot_src)
    gauges_layer.on_click(_update_plot)

    return map


def plot_wflow_model(wflow_model):
    """Plot WFlow basemap.

    Parameters
    ----------
    wflow_model : hydromt_wflow.WFlowModel
        Wflow model instance from hydromt_wflow
    """
    if "wflow_dem" not in wflow_model.staticmaps:
        wflow_model.read_staticmaps("staticmaps.nc")

    proj = ccrs.PlateCarree()
    gdf_bas = wflow_model.basins
    gdf_riv = wflow_model.rivers
    dem = wflow_model.staticmaps["wflow_dem"].raster.mask_nodata()

    vmin, vmax = dem.quantile([0.0, 0.98]).compute()
    c_dem = plt.cm.terrain(np.linspace(0.25, 1, 256))
    cmap = colors.LinearSegmentedColormap.from_list("dem", c_dem)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    kwargs = dict(cmap=cmap, norm=norm)
    cbar_kwargs = dict(shrink=0.8, label="Elevation [m]")

    fig = plt.figure(figsize=(14, 7))
    ax = fig.add_subplot(projection=proj)
    ax.add_image(cimgt.QuadtreeTiles(), 10, alpha=0.5)
    gdf_bas.boundary.plot(ax=ax, color="k", linewidth=1)
    gdf_riv.plot(ax=ax, color="b", linewidth=gdf_riv["strord"] / 2, label="rivers")
    dem.plot(ax=ax, **kwargs, cbar_kwargs=cbar_kwargs)

    if "reservoirs" in wflow_model.geoms:
        resv_kwargs = dict(
            facecolor="blue", edgecolor="black", linewidth=1, label="reservoirs"
        )
        wflow_model.staticgeoms["reservoirs"].plot(ax=ax, **resv_kwargs)
    if "Q_gauges" in wflow_model.results:
        gauges_kwargs = dict(
            facecolor="red",
            marker="d",
            markersize=30,
            zorder=10,
            edgecolor="w",
            label="gauges",
        )
        gdf_gauges = gpd.GeoDataFrame(
            {"geometry": wflow_model.results["Q_gauges"].geometry}
        )
        gdf_gauges.plot(ax=ax, **gauges_kwargs)
    # wflow_model.staticgeoms['gauges_src'].plot(ax=ax, **gauges_kwargs)

    _ = ax.legend(
        # handles=[*ax.get_legend_handles_labels()[0], *patches],
        title="Legend",
        loc="lower right",
        frameon=True,
        framealpha=0.7,
        edgecolor="k",
        facecolor="white",
    )
    ax.xaxis.set_visible(True)
    ax.yaxis.set_visible(True)
    ax.set_xlabel("Longitude [deg]")
    ax.set_ylabel("Latitude [deg]")
    ax.set_title("WFlow base map")
