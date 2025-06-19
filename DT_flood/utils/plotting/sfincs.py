"""SFINCS plotting utilities."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors


def get_model_bounds(database):
    """Get SFINCS boundaries."""
    return database.get_model_boundary().dissolve().to_crs(4326)


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
