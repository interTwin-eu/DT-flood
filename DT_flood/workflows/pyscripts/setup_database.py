"""Script to setup FloodAdapt database."""

import argparse
from pathlib import Path
from shutil import copytree, rmtree

import tomli
import tomli_w
from flood_adapt.config.config import Settings
from flood_adapt.database_builder.database_builder import ConfigModel, DatabaseBuilder

from DT_flood.cfg import CFG_DIR
from DT_flood.utils.fa_scenario_utils import create_systems_folder, folder_structure

parser = argparse.ArgumentParser()

parser.add_argument("--name")
parser.add_argument("--databasepath")
parser.add_argument("--sfincsroot")
parser.add_argument("--wflowroot")
parser.add_argument("--fiatroot")
parser.add_argument("--ra2ceroot")

args = vars(parser.parse_args())

name = args["name"]
root = Path(args["databasepath"])
if not root.is_absolute():
    root = (Path.cwd() / root).resolve()
sf_root = Path(args["sfincsroot"])
fiat_root = Path(args["fiatroot"])
wf_root = Path(args["wflowroot"])
ra2ce_root = Path(args["ra2ceroot"]) / "data"

config_fn = CFG_DIR / "fa_database_build.toml"
with open(config_fn, "rb") as f:
    config = tomli.load(f)

config["database_path"] = root.as_posix()
config["name"] = name
config["fiat"] = fiat_root.as_posix()
config["sfincs_overland"]["name"] = sf_root.as_posix()
config["building_footprints"]["file"] = (
    fiat_root / "exposure" / "buildings.gpkg"
).as_posix()

if not root.is_absolute():
    root = (Path.cwd() / root).resolve()

(root / name).mkdir(parents=True)
folder_structure(root / name)

sys_folder = root / "system"
if not sys_folder.exists():
    print(f"Creating sys folder at {sys_folder}")
    create_systems_folder(sys_folder.parent)

Settings(
    DATABASE_ROOT=root,
    DATABASE_NAME=name,
    SYSTEM_FOLDER=sys_folder,
    DELETE_CRASHED_RUNS=False,
)

rmtree(root / name)
configmodel = ConfigModel(**config)
builder = DatabaseBuilder(config=configmodel, overwrite=True)
builder.build()

with open(root / name / "fa_database_config.toml", "wb") as f:
    tomli_w.dump(config, f)

copytree(wf_root, root / name / "static" / "templates" / "wflow")
copytree(ra2ce_root, root / name / "static" / "templates" / "ra2ce")
