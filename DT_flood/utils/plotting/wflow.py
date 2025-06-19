"""WFLOW plotting utilities."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors


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
