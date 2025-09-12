"""Util functions for data IO."""

from math import ceil, floor
from pathlib import Path
from shutil import rmtree

import geopandas as gpd
import hydromt  # noqa: F401
import pandas as pd
import xarray as xr
from hydromt import DataCatalog
from rucio.client import Client
from rucio.client.downloadclient import DownloadClient


def get_dataset_names(rucio_scope: str = "wtromp"):
    """
    Get the names of datasets in a Rucio scope.

    Parameters
    ----------
    rucio_scope : str, optional
        The Rucio scope to use. The default is 'wtromp'.

    Returns
    -------
    list
        A list of dataset names.
    """
    # Create a Rucio client
    rucio_client = Client()

    # Get the list of datasets in the scope
    datasets = rucio_client.list_dids(
        scope=rucio_scope, filters={"name": "*"}, did_type="dataset"
    )
    return list(datasets)


def get_forcing_data(
    dataset: str,
    start_date: str,
    end_date: str,
    data_vars: list,
    rucio_scope: str = "wtromp",
):
    """
    Get forcing data from Rucio.

    Parameters
    ----------
    dataset : str
        The name of the dataset to download.
    start_date : str
        The start date of the data to download.
    end_date : str
        The end date of the data to download.
    data_vars : list
        The list of data variables to download.
    rucio_scope : str, optional
        The Rucio scope to use. The default is 'wtromp'.

    Returns
    -------
    list
        A list of paths to the downloaded files.
    """
    download_list = []
    outlist = []

    # Create a Rucio client
    rucio_client = Client()

    # Create a DownloadClient instance
    download_client = DownloadClient()

    # get list of moths and years
    months = list(
        range(pd.to_datetime(start_date).month, pd.to_datetime(end_date).month + 1)
    )
    years = list(
        range(pd.to_datetime(start_date).year, pd.to_datetime(end_date).year + 1)
    )

    # Get contents of the dataset
    contents = rucio_client.list_content(
        name=dataset,
        scope=rucio_scope,
    )
    # Get files with correct months and years
    if "elevtn" in data_vars:
        download_list.append({"did": "wtromp:elevtn.nc"})
        outlist.append(Path("wtromp", "elevtn.nc"))
    for file in contents:
        if (
            any("_" + str(month) in file["name"] for month in months)
            and any("_" + str(year) in file["name"] for year in years)
            and any(var in file["name"] for var in data_vars)
        ):
            download_list.append({"did": file["scope"] + ":" + file["name"]})
            outlist.append(Path(file["scope"], file["name"]))

    print(f"Downloading files: {download_list}")
    _ = download_client.download_dids(download_list)
    for file in outlist:
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist. Download failed.")
    return outlist


def download_tiled_data(dataset: str, bbox: list[float], rucio_scope: str = "wtromp"):
    """Download raster dataset. Assumes tiling into 1x1 deg tiles, with naming convention x{E,W}y{N,S} with (x,y) the western and soutmost corner of the tile.

    Parameters
    ----------
    dataset : str
        rucio name of dataset
    bbox : list[float]
        area of interest bbox, format [xmin, ymin, xmax, ymax]
    rucio_scope : str, optional
        rucio scope where dataset is kept, by default "wtromp"

    Returns
    -------
    list[Path]
        list of Paths to downloaded files

    Raises
    ------
    FileNotFoundError
        Raise error if download failed.
    """
    download_list = []
    outlist = []

    # Create a Rucio client
    rucio_client = Client()

    # Create a DownloadClient instance
    download_client = DownloadClient()

    lons = list(range(floor(bbox[0]), ceil(bbox[2]), 1))
    lons = [f"{abs(x)}W" if x < 0 else f"{x}E" for x in lons]
    lats = list(range(floor(bbox[1]), ceil(bbox[3]), 1))
    lats = [f"{abs(x)}S" if x < 0 else f"{x}N" for x in lats]

    contents = rucio_client.list_content(name=dataset, scope=rucio_scope)

    for file in contents:
        if any(f"_{lon}" in file["name"] for lon in lons) and any(
            lat in file["name"] for lat in lats
        ):
            download_list.append({"did": f"{file['scope']}:{file['name']}"})
            outlist.append(Path(file["scope"], file["name"]))
    download_client.download_dids(download_list)
    for file in outlist:
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist. Download failed.")
    return outlist


def get_geodata(dataset: str, bbox: list[float] = None, rucio_scope: str = "wtromp"):
    """Download dataset of singleton geodata file.

    Parameters
    ----------
    dataset : str
        rucio name of dataset
    bbox : list[float]
        area of interest bbox, format [xmin, ymin, xmax, ymax]
    rucio_scope : str, optional
        rucio scope where dataset is kept, by default "wtromp"

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame of downloaded dataset.

    Raises
    ------
    ValueError
        Raise error if dataset contains more than one file.
    """
    # Create a Rucio client
    rucio_client = Client()

    # Create a DownloadClient instance
    download_client = DownloadClient()

    contents = rucio_client.list_content(name=dataset, scope=rucio_scope)
    contents = list(contents)
    if len(list(contents)) > 1:
        raise ValueError(
            "Currenly only geodatasets containing one gpkg file is supported"
        )
    for file in contents:
        download_client.download_dids([{"did": f"{file['scope']}:{file['name']}"}])
        fn = Path(file["scope"], file["name"])
    if bbox is not None:
        gdf = gpd.read_file(fn, bbox=tuple(bbox))
    else:
        gdf = gpd.read_file(fn)

    return gdf


def get_event_forcing_data(
    dataset: str,
    start_date: str,
    end_date: str,
    data_vars: list,
    bounds: list,
    rucio_scope: str = "wtromp",
    cleanup=True,
):
    """
    Get forcing data for a specific event from Rucio.

    Parameters
    ----------
    dataset : str
        The name of the dataset to download.
    start_date : str
        The start date of the data to download.
    end_date : str
        The end date of the data to download.
    data_vars : list
        The list of data variables to download.
    bounds : list
        The bounding box to clip the data to. CRS should match dataset CRS.
    rucio_scope : str, optional
        The Rucio scope to use. The default is 'wtromp'.

    Returns
    -------
    xarray.Dataset
        An xarray dataset containing the forcing data for the event.
    """
    # Get the forcing data for the event
    data_list = get_forcing_data(
        dataset=dataset,
        start_date=start_date,
        end_date=end_date,
        data_vars=data_vars,
        rucio_scope=rucio_scope,
    )
    # merge the data files
    ds_full = xr.open_mfdataset(
        data_list,
        combine="nested",
    )
    ds_full.close()

    ds_full = ds_full.sortby("longitude")
    ds_full = ds_full.sortby("latitude")

    delta_lat = ds_full["latitude"].diff("latitude").min().values
    delta_lon = ds_full["longitude"].diff("longitude").min().values

    ds_clip = ds_full.sel(
        longitude=slice(bounds[0] - delta_lon, bounds[2] + delta_lon),
        latitude=slice(bounds[1] - delta_lat, bounds[3] + delta_lat),
    )

    if len(ds_clip.time) > 1:
        print("slicing time")
        ds_clip = ds_clip.sel(time=slice(start_date, end_date))

    if cleanup:
        ds_clip.load()
        rmtree(rucio_scope)

    return ds_clip


def get_gtsm_forcing_data(
    dataset: str,
    start_date: str,
    end_date: str,
    data_vars: list,
    bounds: list,
    rucio_scope: str = "wtromp",
    cleanup: bool = True,
):
    """Get GTSM data from Rucio.

    Parameters
    ----------
    dataset : str
        The name of the dataset to download.
    start_date : str
        The start date of the data to download.
    end_date : str
        The end date of the data to download.
    data_vars : list
        The list of data variables to download.
    bounds : list
        The bounding box to clip the data to. CRS should match dataset CRS.
    rucio_scope : str, optional
        The Rucio scope to use. The default is 'wtromp'.

    Returns
    -------
    xarray.Dataset
        An xarray dataset containing the GTSM data for the event.
    """
    # Get the forcing data for the event
    data_list = get_forcing_data(
        dataset=dataset,
        start_date=start_date,
        end_date=end_date,
        data_vars=data_vars,
        rucio_scope=rucio_scope,
    )
    # merge the data files
    ds_full = xr.open_mfdataset(
        data_list,
        combine="nested",
    )
    ds_full.close()

    dc = DataCatalog()

    ds_clip = dc.get_geodataset(ds_full, bbox=bounds, time_tuple=(start_date, end_date))

    if cleanup:
        ds_clip.load()
        rmtree(rucio_scope)

    return ds_clip


def download_dataset(
    dataset: str,
    rucio_scope: str = "wtromp",
):
    """Download full dataset from rucio."""
    download_list = []
    outlist = []

    # Create a Rucio client
    rucio_client = Client()

    # Create a DownloadClient instance
    download_client = DownloadClient()

    contents = rucio_client.list_content(name=dataset, scope=rucio_scope)

    for file in contents:
        download_list.append({"did": file["scope"] + ":" + file["name"]})
        outlist.append(Path(file["scope"], file["name"]))

    print(f"Downloading files: {download_list}")
    download_client.download_dids(download_list)
    for file in outlist:
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist. Download failed.")
    return outlist


def download_single(filename: str, rucio_scope: str):
    """Download single file from rucio."""
    download_client = DownloadClient()
    download_client.download_dids([{"did": f"{rucio_scope}:{filename}"}])
    return Path(rucio_scope, filename)
