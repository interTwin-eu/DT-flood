"""FIAT plotting utilities."""

import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap


def list_agg_areas(database):
    """Return list of available aggregation area types."""
    return list(database.get_aggregation_areas().keys())


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
