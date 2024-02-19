from sys import argv
from pathlib import Path
import subprocess

fa_database_fn = Path(argv[1])
sf_folder = fa_database_fn / "output" / "Scenarios" / argv[2] / "Flooding" / "simulations" / "overland"

print(f"Executing SFINCS model at {str(sf_folder)}")
cmd = f"singularity run --bind ./:/data --nv docker://deltares/sfincs-cpu:sfincs-v2.0.3-Cauberg | tee ./sfincs.log"
print(f"Executing {cmd}")
p = subprocess.run(cmd, shell=True, cwd=sf_folder)