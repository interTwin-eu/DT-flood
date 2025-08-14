#%%
import shutil
from pathlib import Path

from rucio.client import Client
from rucio.client.uploadclient import UploadClient
from rucio.client.downloadclient import DownloadClient

client = Client()
upload_client = UploadClient()
download_client = DownloadClient()
# %%

contents = client.list_content(scope="wtromp", name="baltic_usecase")
# %%
download_list = []
for file in contents:
    download_list.append({"did": file["scope"] + ":" + file["name"]})
# %%
download_client.download_dids(download_list)
# %%
data_folder = Path("data")
dikes_folder = data_folder/"dikes"
mask_folder = data_folder/"mask"
topo_folder = data_folder/"topobathy"
wl_folder = data_folder/"waterlevel"
# %%
data_folder.mkdir(exist_ok=True)
shutil.move("wtromp/region.geojson", data_folder/"region.geojson")
# %%
dikes_folder.mkdir(exist_ok=True)
shutil.move("wtromp/all_dikes.gpkg", dikes_folder/"all_dikes.gpkg")
shutil.move("wtromp/test_breaches.geojson", dikes_folder/"test_breaches.geojson")
# %%
mask_folder.mkdir(exist_ok=True)
shutil.move("wtromp/landmask.gpkg", mask_folder/"landmask.gpkg")
shutil.move("wtromp/mask_25833.geojson", mask_folder/"mask_25833.geojson")
shutil.move("wtromp/zsini_regridded_20m_final.tif", mask_folder/"zsini_regridded_20m_final.tif")
# %%
topo_folder.mkdir(exist_ok=True)
shutil.move("wtromp/Baltic_Sea_Bathy.tif", topo_folder/"Baltic_Sea_Bathy.tif")
shutil.move("wtromp/DEM.tif", topo_folder/"DEM.tif")
shutil.move("wtromp/mv_masked_clipped.tif", topo_folder/"mv_masked_clipped.tif")
shutil.move("wtromp/data.yml", topo_folder/"data.yml")
# %%
wl_folder.mkdir(exist_ok=True)
wl_files = list(Path("wtromp").glob("pegelonline*"))
for file in wl_files:
    shutil.move(file, wl_folder/file.name)
# %%
Path("wtromp").rmdir()