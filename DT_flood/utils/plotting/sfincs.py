"""SFINCS plotting utilities."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from hydromt_sfincs import SfincsModel
from ipyleaflet import CircleMarker, GeoData
from matplotlib import colors

from DT_flood.utils.plotting.map_utils import (
    add_fig_to_widg,
    add_plot_box,
    rm_layer_by_name,
)


def get_model_bounds(database):
    """Get SFINCS boundaries."""
    return database.get_model_boundary().dissolve().to_crs(4326)


def get_sfincs_scenario_model(database, scenario):
    """Get the sfincs model instance for a scenario."""
    database = database.database
    sf_path = (
        database.scenarios.output_path.joinpath(scenario)
        / "Flooding"
        / database.site.sfincs.config.overland_model.name
    )

    sf = SfincsModel(root=sf_path, mode="r")
    sf.read()

    return sf


def add_sfincs_dep_map(map, sf):
    """Add SFINCS dep to map layer."""
    vmin, vmax = sf.grid["dep"].raster.mask_nodata().quantile([0.0, 0.98]).values
    c_dem = plt.cm.terrain(np.linspace(0.25, 1, int(vmax)))
    c_bat = plt.cm.terrain(np.linspace(0, 0.17, abs(int(vmin))))
    c_dem = np.vstack((c_bat, c_dem))
    cmap = colors.LinearSegmentedColormap.from_list("dem", c_dem)

    # N = 9
    # legend_vals = cmap(np.linspace(0,1,N))

    map.add_raster(
        sf.grid.rio.reproject("EPSG:4326")["dep"],
        vmin=vmin,
        vmax=vmax,
        colormap=cmap,
        nodata=np.nan,
        layer_name="sfincs_dep",
    )

    # color_hex = [colors.rgb2hex(i) for i in legend_vals]
    # map.add_colorbar(color_hex, round(vmin,2), round(vmax,2), caption="Topobathy [m]", step=N)

    return map


def add_sfincs_riv_map(map, sf):
    """Add SFINCS riv to map layer."""
    riv = sf.geoms["rivers_inflow"].to_crs(4326)
    style = {
        "color": "black",
        "weight": 3,
    }

    map.add_gdf(
        riv, info_mode=None, hover_style=style, style=style, layer_name="sfincs_riv"
    )

    return map


def add_sfincs_bzs_points(map, sf):
    """Add SFINCS bzs points to map layer."""
    bzs_points = gpd.GeoDataFrame(
        {"index": sf.forcing["bzs"].index, "geometry": sf.forcing["bzs"].geometry},
        crs=sf.crs,
    ).to_crs("EPSG:4326")

    geo_data = GeoData(
        geo_dataframe=bzs_points,
        style={
            "color": "black",
            "radius": 8,
            "fillColor": "#3366cc",
            "opacity": 0.5,
            "weight": 2,
            "dashArray": "2",
            "fillOpacity": 0.6,
        },
        hover_style={"fillColor": "red", "fillOpacity": 0.2},
        point_style={
            "radius": 5,
            "color": "red",
            "fillOpacity": 0.8,
            "fillColor": "blue",
            "weight": 3,
        },
        name="sfincs_bzs",
    )

    map.add(geo_data)

    def add_plot_marker(map, location):
        circle = CircleMarker(name="plot_marker")
        circle.location = location
        circle.radius = 8
        circle.color = "black"
        circle.fill_color = "red"
        circle.weight = 3
        circle.dashArray = 1
        circle.fillOpacity = 1
        map.add(circle)

    def update_plot_box(feature, **kwargs):
        index = feature["properties"]["index"]
        fig = plt.figure()
        ax = fig.add_subplot()
        sf.forcing["bzs"].sel(index=index).plot(ax=ax)
        ax.set_ylabel(["waterlevel [m]"])
        ax.set_title(f"Waterlevel boundary point {index}")
        plt.grid()

        rm_layer_by_name(map, "plot_marker")
        im_wdg = add_plot_box(map)

        add_fig_to_widg(im_widg=im_wdg, fig=fig)
        add_plot_marker(map, location=feature["geometry"]["coordinates"][::-1])

    geo_data.on_click(update_plot_box)

    return map


def plot_sfincs_model(sf):
    """Plot SFINCS basemap.

    Parameters
    ----------
    sf : hydromt_sfincs.SfincsModel
        SFINCS model instance from hydromt
    """
    proj = ccrs.PlateCarree()
    bzs_points = gpd.GeoDataFrame(
        {"index": sf.forcing["bzs"].index, "geometry": sf.forcing["bzs"].geometry},
        crs=sf.crs,
    ).to_crs("EPSG:4326")
    dis_points = gpd.GeoDataFrame(
        {"index": sf.forcing["dis"].index, "geometry": sf.forcing["dis"].geometry},
        crs=sf.crs,
    ).to_crs("EPSG:4326")

    vmin, vmax = sf.grid["dep"].raster.mask_nodata().quantile([0, 0.98]).values
    c_dem = plt.cm.terrain(np.linspace(0.25, 1, int(vmax)))
    c_bat = plt.cm.terrain(np.linspace(0, 0.17, abs(int(vmin))))
    c_dem = np.vstack((c_bat, c_dem))
    cmap = colors.LinearSegmentedColormap.from_list("dem", c_dem)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(projection=proj)
    ax.add_image(cimgt.OSM(), 10, interpolation="bilinear", alpha=0.5)

    sf.grid.rio.reproject("EPSG:4326")["dep"].plot(
        ax=ax,
        cmap=cmap,
        norm=norm,
        cbar_kwargs={"shrink": 0.85, "label": "DEM [m]", "pad": 0.03},
    )
    sf.geoms["obs"].to_crs("EPSG:4326").plot(
        ax=ax,
        marker="d",
        facecolor="w",
        edgecolor="r",
        markersize=60,
        label="obs points",
        zorder=10,
    )
    sf.geoms["rivers_inflow"].to_crs("EPSG:4326").plot(
        ax=ax, color="darkblue", label="Rivers"
    )
    bzs_points.plot(
        ax=ax,
        marker="^",
        facecolor="w",
        edgecolor="k",
        markersize=60,
        label="bzs points",
        zorder=10,
    )
    dis_points.plot(
        ax=ax,
        marker=">",
        facecolor="w",
        edgecolor="k",
        markersize=60,
        label="dis points",
        zorder=10,
    )
    ax.legend(
        title="Legend",
        loc="upper right",
        frameon=True,
        framealpha=0.7,
        edgecolor="k",
        facecolor="white",
    )
    ax.xaxis.set_visible(True)
    ax.yaxis.set_visible(True)
    ax.set_ylabel("Latitude [deg]")
    ax.set_xlabel("Longitude [deg]")
    ax.set_title("SFINCS basemap DEM")
