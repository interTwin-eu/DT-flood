import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

proj = ccrs.PlateCarree()

from hydromt_wflow import WflowModel


def plot_wflow_model(wflow_model):
    gdf_bas = wflow_model.basins
    gdf_riv = wflow_model.rivers
    dem = wflow_model.staticmaps['wflow_dem'].raster.mask_nodata() 

    vmin, vmax = dem.quantile([0., 0.98]).compute()
    c_dem = plt.cm.terrain(np.linspace(0.25, 1, 256))
    cmap = colors.LinearSegmentedColormap.from_list("dem", c_dem)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    cmap_kwargs = dict(cmap=cmap, norm=norm) 

    fig = plt.figure(figsize=(14,7))
    ax = fig.add_subplot(projection=proj)
    ax.add_image(cimgt.QuadtreeTiles(),10,alpha=0.5)
    gdf_bas.boundary.plot(ax=ax, color='k')
    gdf_riv.plot(ax=ax,color='b', linewidth = gdf_riv['strord']/2)
    dem.plot(ax=ax,**cmap_kwargs)

    resv_kwargs = dict(facecolor='blue', edgecolor='black', linewidth=1)
    gauges_kwargs = dict(facecolor='red', shape='diamond', size=10)

    wflow_model.staticgeoms['reservoirs'].plot(ax=ax,**resv_kwargs)
    wflow_model.staticgeoms['gauges_src'].plot(ax=ax, **gauges_kwargs)