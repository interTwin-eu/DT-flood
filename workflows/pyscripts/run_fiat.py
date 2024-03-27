from sys import argv
from pathlib import Path
from fiat import FIAT
import subprocess
import os

fa_database_fn = Path(argv[1])
fiat_folder = fa_database_fn / "output" / "Scenarios" / argv[2] / "Impacts" / "fiat_model"

fiat_config = fiat_folder / "settings.toml"

# print(os.environ["GDAL_DATA"])
# print(os.environ["PROJ_LIB"])

# fiat = FIAT.from_path(fiat_config)
# fiat.run()

print(f"Running FIAT model at {fiat_folder}")
# cmd = f"fiat run {fiat_config} | tee {fiat_folder}/fiat.log"
cmd = f"fiat run {fiat_config}"
print(f"Executing cmd {cmd}")
p = subprocess.run(cmd, shell=True)