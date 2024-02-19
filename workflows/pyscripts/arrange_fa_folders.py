from sys import argv
from pathlib import Path
from shutil import copytree

in_folder = Path(argv[1])
fa_database = Path(argv[2])
scenario = argv[3]

copytree(in_folder,(fa_database/ "output" / "Scenarios" / scenario / "Flooding" / "simulations" / in_folder.stem), dirs_exist_ok=True)
# in_folder.rename(fa_database/ "output" / "Scenarios" / scenario / "Flooding" / "simulations" / in_folder.stem)