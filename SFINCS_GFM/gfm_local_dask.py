# %%

from dask.distributed import Client
import hvplot.xarray
from dask_flood_mapper import flood
# %%

client = Client(processes=False, threads_per_worker=2, n_workers=1, memory_limit="6GB")

time_range = "2022-10-11/2022-10-25"
bbox = [12.3, 54.3, 13.1, 54.6]

# %%

fd = flood.decision(bbox=bbox, datetime=time_range).compute()

# %%

fd.hvplot.image(
    x="x",
    y="y",
    rasterize=True,
    geo=True,
    tiles=True,
    project=True,
    cmap=["rgba(0, 0, 1, 0.1)", "darkred"],
    cticks=[(0, "non-flood"), (1, "flood")],
    frame_height=400
)