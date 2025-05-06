from pathlib import Path
from shutil import copy
import requests
import zipfile
import io
import pandas as pd

from hydromt_sfincs.sfincs_input import SfincsInput

def copy_sfincs_model(src: Path, dest: Path) -> None:

    inp = SfincsInput.from_file(src/"sfincs.inp")
    config = inp.to_dict()

    if not dest.exists():
        dest.mkdir(parents=True)

    for key, value in config.items():
        # skip dep file if subgrid file is present
        if "dep" in key and "sbgfile" in config:
            continue
        if "file" in key:
            copy(src / value, dest / value)
    
    copy(src / "sfincs.inp", dest / "sfincs.inp")

def parse_local_wl_data(wl_file: Path) -> pd.DataFrame:
    
    df = pd.read_csv(wl_file, delimiter=";", header=0)
    df = df.rename(columns={"timestamp": "time", "value": 1})
    df[1] = pd.to_numeric(df[1])

    time = pd.to_datetime(df["time"])
    bzs = (df[1]/100).to_list()

    bzspd = pd.DataFrame(
        index=time,
        columns=df.columns[1:],
        data=bzs,
    )
    return bzspd

def fetch_local_wind_data(url: str) -> pd.DataFrame:
    data_folder = Path("data/wind")
    response = requests.get(url)
    z = zipfile.ZipFile(io.BytesIO(response.content))
    z.extractall(data_folder)
    [file] = [x for x in data_folder.glob("*.txt") if "Metadaten" not in x.name]

    df = pd.read_csv(file, delimiter=";").rename(columns=lambda x: x.strip())
    time = pd.to_datetime(df["MESS_DATUM"], format="%Y%m%d%H").rename("time")

    wnd = pd.DataFrame(
        index=time,
        columns=["mag", "dir"],
        data=df[["F", "D"]]
    )

    return wnd

   