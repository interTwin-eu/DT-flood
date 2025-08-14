# %%

import hvplot.xarray # noqa: F401
import xarray as xr

# %%

time_range = "2023-10-15/2023-10-23"
bbox = [12.3, 54.3, 13.1, 54.6]

# %%

fd = xr.open_dataset(r"c:\Users\winter_ga\Offline_data\projects\InterTwin\flood_output_TUWien\floodcube.nc")
print("Finished flood decision")
print(fd)

# %%

fd_max = fd.max(dim="time")

fd_max = fd_max.set_coords("spatial_ref")
print(fd_max)

fd_max.rio.to_raster(r"c:\Users\winter_ga\Offline_data\projects\InterTwin\flood_output_TUWien\floodcube.tiff")
# fd.hvplot.image(
#     x="longitude",
#     y="latitude",
#     rasterize=True,
#     geo=True,
#     tiles=True,
#     project=True,
#     cmap=["rgba(0, 0, 1, 0.1)", "darkred"],
#     cticks=[(0, "non-flood"), (1, "flood")],
#     frame_height=400
# )
# %%
