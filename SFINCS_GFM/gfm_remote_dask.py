# %%
import hvplot.xarray # noqa
from dask_flood_mapper import flood
from eodc import settings
from eodc.dask import EODCDaskGateway
from rich.console import Console
from rich.prompt import Prompt
# %%

settings.DASK_URL = "https://dask.services.eodc.eu"
settings.DASK_URL_TCP = "tcp://dask.services.eodc.eu:10000/"
# %%
console = Console()
your_username = Prompt.ask(prompt="Enter your Username")
gateway = EODCDaskGateway(username=your_username)
# %%

cluster_options = gateway.cluster_options()
cluster_options.image = "ghcr.io/eodcgmbh/cluster_image:2025.4.1"
cluster_options.worker_cores = 8
cluster_options.worker_memory = 16
# %%
cluster = gateway.new_cluster(cluster_options=cluster_options)
client = cluster.get_client()
# %%
console.print(gateway.list_clusters())
# %% Connect to existing cluster
# cluster = gateway.connect(gateway.list_clusters()[0].name)
# console.print(cluster)
# %%
cluster.dashboard_link
# %%
time_range = "2023-10-11/2023-10-25"
bbox = [12.3, 54.3, 13.1, 54.6]
fd = flood.probability(bbox=bbox, datetime=time_range).compute()
fd
# %%
client.close()

# %%
