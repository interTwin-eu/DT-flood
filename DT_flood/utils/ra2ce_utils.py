import os
from pathlib import Path
import subprocess


def setup_base_folder(root: os.PathLike) -> None:
    """Create folder for base RA2CE model.

    Parameters
    ----------
    root : os.PathLike
        Directory where folder is created.
    name : str
        Name of RA2CE project/model.
    """
    hazard_folder = root / "static" / "hazard"
    hazard_folder.mkdir(parents=True, exist_ok=True)
    network_folder = root / "static" / "network"
    network_folder.mkdir(parents=True, exist_ok=True)
    graph_folder = root / "static" / "output_graph"
    graph_folder.mkdir(parents=True, exist_ok=True)
    output_folder = root / "output"
    output_folder.mkdir(parents=True, exist_ok=True)


def setup_ra2ce(ra2ce_root: os.PathLike) -> None:
    utils_path = (
        Path(__file__).parents[1] / "workflows" / "pyscripts" / "utils_ra2ce_docker.py"
    )
    script_path = Path(__file__).parent / "setup_ra2ce.py"

    cmd = f"""
        docker run -v {str(ra2ce_root)}:/home/mambauser/project/ra2ce \
        -v {str(utils_path)}:/home/mambauser/project/utils_ra2ce_docker.py \
        -v {str(script_path)}:/home/mambauser/project/setup_ra2ce.py \
        containers.deltares.nl/gfs/ra2ce:v1_0_0 \
        python /home/mambauser/project/setup_ra2ce.py
        """
    subprocess.run(cmd, shell=True)
