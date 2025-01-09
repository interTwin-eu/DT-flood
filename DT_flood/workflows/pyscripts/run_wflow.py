from sys import argv
from pathlib import Path
import tomli
import subprocess

fa_database_fn = Path(argv[1])
mode = argv[3]
# scenario_fn = fa_database_fn / "input" / "scenarios" / argv[2] / (argv[2]+".toml")

wf_folder = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / ("wflow_"+mode)
wf_toml_fn = wf_folder / "wflow_sbm.toml"

with open(wf_toml_fn, "rb") as f:
    wf_toml = tomli.load(f)

if wf_toml["model"]["reinit"]:
    print("Using Default instates")
elif (wf_folder / wf_toml["state"]["path_input"]).exists():
    print(f"Using instates from {wf_toml['state']['path_input']}")
else:
    raise RuntimeError("Cannot find valid instate file")

path_containter = Path("/data")
for path in wf_folder.parts[-6:]:
    path_containter=path_containter/path

cmd = f"singularity run --bind {str(fa_database_fn)}/:/data/ docker://deltares/wflow {path_containter}/wflow_sbm.toml"
print(f"Executing command {cmd}")
p = subprocess.run(cmd, shell=True)