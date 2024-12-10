from pathlib import Path
from sys import argv
import pandas as pd

from flood_adapt.api import scenarios
from DT_flood.utils.fa_scenario_utils import init_scenario

database, scenario_config = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario = scenarios.get_scenario(scenario_config['name'])

fiat_out_fn = Path(scenario.direct_impacts.fiat_path, "output", "output.csv")
fiat_out = pd.read_csv(fiat_out_fn)

if "Total Damage" not in fiat_out.columns:
    fiat_out["Total Damage"] = fiat_out["total_damage"]

fiat_out.to_csv(fiat_out_fn)

scenario.direct_impacts.postprocess_fiat()