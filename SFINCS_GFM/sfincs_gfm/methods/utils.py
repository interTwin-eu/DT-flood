from pathlib import Path
from shutil import copy

from hydromt_sfincs.sfincs_input import SfincsInput

def copy_sfincs_model(src: Path, dest: Path) -> None:

    inp = SfincsInput.from_file(src/"sfincs.inp")
    config = inp.to_dict()

    if not dest.exists():
        dest.mkdir(parents=True)

    for key, value in config.items():
        # skip dep file if subgrid file is present
        if "dep" in key and "sbgfile" in config:
            continue
        if "file" in key:
            copy(src / value, dest / value)
    
    copy(src / "sfincs.inp", dest / "sfincs.inp")