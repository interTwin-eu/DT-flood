"""Plot utility functions."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import geopandas as gdp
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.cm import get_cmap


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
        gdf_gauges = gdp.GeoDataFrame(
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


def plot_fiat_model(fiat):
    """Plot FIAT basemap.

    Parameters
    ----------
    fiat : hydromt_fiat.FiatModel
        FIAT model instance from hydromt_fiat
    """
    proj = ccrs.PlateCarree()
    gdf_fiat = fiat.exposure.get_full_gdf(fiat.exposure.exposure_db)
    by_type = []
    for type in gdf_fiat["Primary Object Type"].unique():
        by_type.append(gdf_fiat[gdf_fiat["Primary Object Type"] == type])

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(projection=proj)
    ax.add_image(cimgt.OSM(), 10, interpolation="bilinear", alpha=0.3)

    cmaps = {"residential": "Reds", "industrial": "Blues", "commercial": "Greens"}

    handles = []
    patches = []
    for gdf in by_type:
        class_name = gdf["Primary Object Type"].unique()[0]
        # cmap = get_cmap(cmaps[class_name])
        color = get_cmap(cmaps[class_name])(0.2)
        kwargs = dict(facecolor=color, edgecolor="k", linewidth=1, label=class_name)
        patches.append(mpatches.Patch(**kwargs))
        handles.append(
            gdf.plot(
                ax=ax,
                column="Max Potential Damage: Total",
                scheme="quantiles",
                cmap=get_cmap(cmaps[class_name]),
            )
        )

    ax.legend(
        handles=[*handles, *patches],
        title="Legend",
        loc="lower right",
        frameon=True,
        framealpha=0.7,
        edgecolor="k",
        facecolor="white",
    )
    ax.set_title("Delft-FIAT basemap")
    ax.xaxis.set_visible(True)
    ax.yaxis.set_visible(True)
    ax.set_ylabel("Latitude [deg]")
    ax.set_xlabel("Longitude [deg]")


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
    # dis_points = gpd.GeoDataFrame({"index": sf.forcing['dis'].index, "geometry": sf.forcing['dis'].geometry}, crs=sf.crs).to_crs("EPSG:4326")

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
    # sf.geoms['obs'].to_crs('EPSG:4326').plot(ax=ax, marker="d", facecolor='w', edgecolor='r', markersize=60, label="obs points", zorder=10)
    # sf.geoms['rivers_inflow'].to_crs("EPSG:4326").plot(ax=ax, color='darkblue', label="Rivers")
    bzs_points.plot(
        ax=ax,
        marker="^",
        facecolor="w",
        edgecolor="k",
        markersize=60,
        label="bzs points",
        zorder=10,
    )
    # dis_points.plot(ax=ax, marker=">", facecolor='w', edgecolor='k', markersize=60, label="dis points", zorder=10)
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
