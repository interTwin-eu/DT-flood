import os
from pathlib import Path
import subprocess

def setup_base_folder(root: os.PathLike, name: str) -> None:
    """Create folder for base RA2CE model.

    Parameters
    ----------
    root : os.PathLike
        Directory where folder is created.
    name : str
        Name of RA2CE project/model.
    """
    hazard_folder = root/name/"static"/"hazard"
    hazard_folder.mkdir(parents=True)
    network_folder = root/name/"static"/"network"
    network_folder.mkdir(parents=True)
    graph_folder = root/name/"static"/"output_graph"
    graph_folder.mkdir(parents=True)
    output_folder = root/name/"output"
    output_folder.mkdir(parents=True)

def setup_ra2ce(database: os.PathLike) -> None:

    ra2ce_folder = database/"static"/"templates"/"ra2ce"
    utils_path = Path(__file__).parent/"ra2ce_utils_docker.py"
    script_path = Path(__file__).parent/"setup_ra2ce.py"

    cmd = f"""
        docker run -v {str(ra2ce_folder)}:/home/mambauser/project/ra2ce \
        -v {str(utils_path)}:/home/mambauser/project/ra2ce_utils_docker.py \
        -v {str(script_path)}:/home/mambauser/project/setup_ra2ce.py \
        containers.deltares.nl/ra2ce/ra2ce:latest \
        python /home/mambauser/project/setup_ra2ce.py
        """
    subprocess.run(cmd, shell=True)