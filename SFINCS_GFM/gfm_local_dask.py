# %%

from dask.distributed import Client
import hvplot.xarray # noqa: F401
from dask_flood_mapper import flood
# %%

client = Client(processes=False, threads_per_worker=2, n_workers=1, memory_limit="4GB")

time_range = "2022-10-11/2022-10-25"
bbox = [12.3, 54.3, 13.1, 54.6]

# %%

fd = flood.decision(bbox=bbox, datetime=time_range).compute()
print("Finished flood decision")
print(fd)
# %%

# fd.hvplot.image(
#     x="x",
#     y="y",
#     rasterize=True,
#     geo=True,
#     tiles=True,
#     project=True,
#     cmap=["rgba(0, 0, 1, 0.1)", "darkred"],
#     cticks=[(0, "non-flood"), (1, "flood")],
#     frame_height=400
# )