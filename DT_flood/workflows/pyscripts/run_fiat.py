from sys import argv
from pathlib import Path
from fiat import FIAT
import subprocess
import os


from flood_adapt.api import scenarios
from DT_flood.utils.fa_scenario_utils import init_scenario

database, scenario = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario_obj = scenarios.get_scenario(scenario['name'])
fiat_path = scenario_obj.results_path/"Impacts"/"fiat_model"

# print(os.environ["GDAL_DATA"])
# print(os.environ["PROJ_LIB"])

print(f"Running FIAT model at {fiat_path}")
cmd = f"fiat run {str(fiat_path/'settings.toml')} | tee {fiat_path}/fiat.log"
print(f"Executing cmd {cmd}")
p = subprocess.run(cmd, shell=True)