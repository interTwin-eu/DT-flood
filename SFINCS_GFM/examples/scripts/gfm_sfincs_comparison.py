# %% Imports
import xarray as xr
import rioxarray as rxr
import numpy as np
import matplotlib.pyplot as plt

# %%

time_range = "2023-10-15/2023-10-23"
bbox = [12.3, 54.3, 13.1, 54.6]

# %% Import GFM and SFINCS flood map Oct 23    

sf_folder = (r"c:\Users\winter_ga\Offline_data\projects\InterTwin\model\model_20m_wind2")

gfm=rxr.open_rasterio(r"c:\Users\winter_ga\Offline_data\projects\InterTwin\flood_output_TUWien\floodcube.tiff")
gfm.rio.write_crs("epsg:4326",inplace=True)
sf=rxr.open_rasterio(sf_folder + "/" + "max_waterdepth.tif")

print(f"GFM: {gfm.rio.crs}")
print(f"SFINCS: {sf.rio.crs}")

# %% reproject GFM flood map
gfm_match = gfm.rio.reproject_match(sf).sel(band=1)
print(f"GFM: {gfm.rio.crs}")
print(f"GFM_match: {gfm_match.rio.crs}")
print(f"SFINCS: {sf.rio.crs}")

# %% COMPARE maps

sf_flood = xr.where(sf.sel(band=1)>0.05,0.5,0)
print(sf_flood)
print(gfm_match)

# gfm_match = xr.where(gfm_match==np.nan,0,1)
compare = sf_flood + gfm_match

compare.rio.to_raster(sf_folder + "/" + "flood_match.tif")

# %%

gfm_match = gfm_match.fillna(0)
compare = sf_flood + gfm_match
count_flooded_match = (compare == 1.5).sum().item()
count_sf_flooded_gfm_not = (compare == 0.5).sum().item()
count_gfm_flooded_sf_not= (compare == 1.0).sum().item()
count_not_flooded_match= (compare == 0.0).sum().item()

print(count_flooded_match)
print(count_sf_flooded_gfm_not)
print(count_gfm_flooded_sf_not)
print(count_not_flooded_match)

total_count = count_not_flooded_match+count_flooded_match+count_sf_flooded_gfm_not+count_gfm_flooded_sf_not
print(f"CHECK: {total_count} = {np.shape(compare)[0]*np.shape(compare)[1]}")
# %% plot  test matrix

from matplotlib.patches import Rectangle

# Create a figure and an axis
fig, ax = plt.subplots(figsize=(3,3))

# Create a rectangle
r1 = Rectangle((0,0), 1, 1, edgecolor='black', facecolor='limegreen', fill=True, lw=0.5)
t1 = plt.text(0.5, 0.5, f"{np.round(count_not_flooded_match/total_count*100,decimals=1)}%", size=16,
         ha="center", va="center",
         )
r2 = Rectangle((1,0), 1, 1, edgecolor='black', facecolor='coral', fill=True, lw=0.5)
t2 = plt.text(1.5, 0.5, f"{np.round(count_gfm_flooded_sf_not/total_count*100,decimals=1)}%", size=16,
         ha="center", va="center",
         )
r3 = Rectangle((0,1), 1, 1, edgecolor='black', facecolor='coral', fill=True, lw=0.5)
t3 = plt.text(0.5, 1.5, f"{np.round(count_sf_flooded_gfm_not/total_count*100,decimals=1)}%", size=16,
         ha="center", va="center",
         )
r4 = Rectangle((1,1), 1, 1, edgecolor='black', facecolor='limegreen', fill=True, lw=0.5)
t4 = plt.text(1.5, 1.5, f"{np.round(count_flooded_match/total_count*100,decimals=1)}%", size=16,
         ha="center", va="center",
         )

# Add the rectangle to the plot
ax.add_patch(r1)
ax.add_patch(r2)
ax.add_patch(r3)
ax.add_patch(r4)

ax.set_xlabel('Global Flood Monitor')
ax.set_xticks([0.5,1.5])
ax.set_xticklabels(["not flooded","flooded"])

ax.set_ylabel('SFINCS')
ax.set_yticks([0.5,1.5])
ax.set_yticklabels(["not flooded","flooded"])
ax.tick_params(axis='y', rotation=90)

ax.set_xlim(left=0,right=2)
ax.set_ylim(bottom=0,top=2)
ax.axis("equal")
ax.set_position([.15,.15,.8,.8])

# Display the plot
plt.savefig(sf_folder + "/" + "flood_match_matrix.png")

# %%
