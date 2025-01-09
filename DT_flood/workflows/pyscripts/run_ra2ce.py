from pathlib import Path
from sys import argv
from pprint import pprint

from ra2ce.ra2ce_handler import Ra2ceHandler
from ra2ce.network.network_config_data.network_config_data_reader import NetworkConfigDataReader
from ra2ce.analysis.analysis_config_data.analysis_config_data_reader import AnalysisConfigDataReader

def tree(directory):
    print(f"+ {directory}")
    for path in sorted(directory.rglob('*')):
        depth = len(path.relative_to(directory).parts)
        spacer = "  " * depth
        print(f"{spacer}+ {path.name}")

fa_database_fn = Path(argv[1])

root_dir = fa_database_fn/"output"/"scenarios"/argv[2]/"Impacts"/"ra2ce"
network_ini = root_dir/"network.ini"
analysis_ini = root_dir/"analysis.ini"

tree(root_dir)

print(network_ini)
print(analysis_ini)

network = NetworkConfigDataReader().read(network_ini)
analysis = AnalysisConfigDataReader().read(analysis_ini)

# handler = Ra2ceHandler.from_config(network,analysis)
# handler.configure()
_ = Ra2ceHandler.run_with_ini_files(network_ini_file=network_ini,analysis_ini_file=analysis_ini)