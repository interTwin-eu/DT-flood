"""Util functions for data IO."""

from pathlib import Path

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
    for file in contents:
        if (
            any("_" + str(month) in file["name"] for month in months)
            and any("_" + str(year) in file["name"] for year in years)
            and any(var in file["name"] for var in data_vars)
        ):
            download_list.append({"did": file["scope"] + ":" + file["name"]})
            outlist.append(Path(file["scope"], file["name"]))

    _ = download_client.download_dids(download_list)
    for file in outlist:
        if not file.exists():
            raise FileNotFoundError(f"File {file} does not exist. Download failed.")
    return outlist


def get_event_forcing_data(
    dataset: str,
    start_date: str,
    end_date: str,
    data_vars: list,
    bounds: list,
    rucio_scope: str = "wtromp",
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
    dc = DataCatalog()

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
        concat_dim="time",
        combine="nested",
    )
    ds_clip = dc.get_rasterdataset(
        ds_full,
        bbox=bounds,
        time_tuple=(start_date, end_date),
    )
    return ds_clip
