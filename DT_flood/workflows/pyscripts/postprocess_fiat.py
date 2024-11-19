from pathlib import Path
from sys import argv

from flood_adapt.api import scenarios
from DT_flood.utils.fa_scenario_utils import init_scenario

database, scenario_config = init_scenario(Path(argv[1]), (argv[2]+"_toplevel.toml"))

scenario = scenarios.get_scenario(scenario_config['name'])

scenario.direct_impacts.postprocess_fiat()