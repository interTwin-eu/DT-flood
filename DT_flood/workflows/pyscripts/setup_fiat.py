"""Script to setup Delft-FIAT model."""

import argparse
from pathlib import Path
from shutil import rmtree

import geopandas as gpd
import tomli
import tomli_w
from hydromt.config import configread, configwrite
from hydromt.log import setuplog
from hydromt_fiat.fiat import FiatModel

from DT_flood.cfg import CFG_DIR
from DT_flood.utils.data_utils import download_dataset

parser = argparse.ArgumentParser()

parser.add_argument("--regionfile")
parser.add_argument("--sfincsroot")
parser.add_argument("--aggareas", default="gadm")

args = vars(parser.parse_args())

ft_root = Path.cwd() / "fiat"
region = gpd.read_file(args["regionfile"])
aggarea_scope = args["aggareas"]
elev_fn = Path(args["sfincsroot"]) / "subgrid" / "dep_subgrid.tif"

ft_config = CFG_DIR / "fiat_build.yml"

datafolder = Path.cwd() / "data"
datafolder.mkdir(exist_ok=True)

agg_fns = download_dataset(dataset=aggarea_scope)
for file in agg_fns:
    file.rename(datafolder / file.name)

# Clean up rucio downloads
rmtree(Path.cwd() / "wtromp")

logger = setuplog("fiat_build", log_level=10)

opt = configread(ft_config)

opt["setup_exposure_buildings"].update(ground_elevation=elev_fn)


ft = FiatModel(root=ft_root, mode="w+", logger=logger)

ft.build(region={"geom": region}, opt=opt, write=True)
ft.write()

# Make sure naming of output is correct in toml settings
with open(ft_root / "settings.toml", "rb") as f:
    config = tomli.load(f)

# fix mismatch between fiat, hydromt-fiat with this naming convention
config["output"]["csv"] = {"name1": config["output"]["csv"]["name"]}

with open(ft_root / "settings.toml", "wb") as f:
    tomli_w.dump(config, f)

configwrite(ft_root / "fiat_build.yml", opt)
