"""Script for collecting workflow outputs into FloodAdapt database structure."""

import argparse
from pathlib import Path
from shutil import copy, copytree, rmtree

parser = argparse.ArgumentParser()
parser.add_argument("--output")
parser.add_argument("--scenario")
parser.add_argument("--sfincsdir")
parser.add_argument("--wflowwarmup")
parser.add_argument("--wflowevent")
parser.add_argument("--fiatdir")
parser.add_argument("--ra2cedir")
parser.add_argument("--floodmap")
parser.add_argument("--waterlevels")

args = parser.parse_args()

output = Path(args.output)
scenario = args.scenario
sfincsdir = Path(args.sfincsdir) / "data"
wflowwarmup = Path(args.wflowwarmup) / "model"
wflowevent = Path(args.wflowevent) / "model"
fiatdir = Path(args.fiatdir)
ra2cedir = Path(args.ra2cedir) / "data"
floodmap = Path(args.floodmap)
waterlevels = Path(args.waterlevels)

scenario_out_dir = output / "scenarios" / scenario
flooding_dir = scenario_out_dir / "Flooding"
impact_dir = scenario_out_dir / "Impacts"

if not flooding_dir.exists():
    flooding_dir.mkdir(parents=True)
if not impact_dir.exists():
    impact_dir.mkdir(parents=True)

print(f"Copying FIAT out from {fiatdir} to {scenario_out_dir}")
copytree(fiatdir, scenario_out_dir, dirs_exist_ok=True)

print(f"Copying SFINCS dir from {sfincsdir} to {flooding_dir}")
copytree(sfincsdir, flooding_dir / "overland", dirs_exist_ok=True)

print(f"Copying WFLOW warmup from {wflowwarmup} to {flooding_dir}")
copytree(wflowwarmup, flooding_dir / "wflow_warmup", dirs_exist_ok=True)

print(f"Copying WFLOW event from {wflowevent} to {flooding_dir}")
copytree(wflowevent, flooding_dir / "wflow_event", dirs_exist_ok=True)

print(f"Copying floodmap from {floodmap} to {flooding_dir}")
copy(floodmap, flooding_dir / floodmap.name)

print(f"Copying waterlevels from {waterlevels} to {flooding_dir}")
copy(waterlevels, flooding_dir / waterlevels.name)

print(f"Copying RA2CE dir from {ra2cedir} to {impact_dir}")
copytree(ra2cedir, impact_dir / "ra2ce", dirs_exist_ok=True)

print("Cleanup")
if (flooding_dir / "overland" / "data").exists():
    rmtree(flooding_dir / "overland" / "data")
if (flooding_dir / "wflow_warmup" / "model").exists():
    rmtree(flooding_dir / "wflow_warmup" / "model")
if (flooding_dir / "wflow_event" / "model").exists():
    rmtree(flooding_dir / "wflow_event" / "model")
if (impact_dir / "ra2ce" / "data").exists():
    rmtree(impact_dir / "ra2ce" / "data")
