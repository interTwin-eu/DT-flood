"""Workflow util functions."""

import os
import subprocess
from pathlib import Path
from typing import Union

import geojson
import yaml
from flood_adapt.dbs_classes.interface.database import IDatabase

from DT_flood.utils.fa_scenario_utils import init_scenario
from DT_flood.workflows import SCRIPT_DIR, WORFKFLOW_DIR


class quoted(str):
    """Represent string with helper class."""

    pass


def quoted_presenter(dumper, data):
    """Make custom YAML presenter for quoted strings."""
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(quoted, quoted_presenter)


def run_scenario(
    database: Union[str, os.PathLike],
    scenario_name: str,
    oscar_endpoint: str,
    oscar_token: str,
    debug: bool = False,
    **kwargs,
) -> None:
    """Run FloodAdapt scenario.

    Parameters
    ----------
    database : Union[str, os.PathLike]
        FloodAdapt database containing the scenario
    scenario_name : str
        name of scenario to execute
    """
    create_workflow_config(
        database=database,
        scenario=scenario_name,
        oscar_endpoint=oscar_endpoint,
        oscar_token=oscar_token,
        **kwargs,
    )
    run_fa_scenario_workflow(database=database, scenario=scenario_name, debug=debug)


def create_workflow_config(
    database: Union[str, os.PathLike, IDatabase],
    scenario: str,
    oscar_endpoint: str,
    oscar_token: str,
    cwl_workflow: Union[str, os.PathLike] = WORFKFLOW_DIR / "run_fa_scenario.cwl",
    script_folder: Union[str, os.PathLike] = SCRIPT_DIR,
    oscar_output: str = "output",
    interlink_offload: bool = False,
) -> None:
    """Write Config file for CWL workflow to FloodAdapt database.

    Parameters
    ----------
    database : Union[str, os.PathLike, IDatabase]
        FloodAdapt database containing the scenario
    scenario : str
        Name of scenario
    oscar_endpoint : str
        URL of Oscar endpoint
    oscar_token : str
        EGI-SSO refresh token for authentication
    cwl_workflow : Union[str, os.PathLike], optional
        Path to cwl workflow description
    script_folder : Union[str, os.PathLike], optional
        Path to folder containing py script being called by workflows
    oscar_output : str, optional
        Name of output folder in Oscar
    interlink_offlaoad : bool, optional
        If True, use Oscar interlink service for offloading
    """
    # Parse inputs
    if isinstance(database, str) or isinstance(database, Path):
        database, _ = init_scenario(database, scenario)

    database = database.database

    if not isinstance(cwl_workflow, Path):
        cwl_workflow = Path(cwl_workflow)
    if not cwl_workflow.exists():
        raise ValueError(
            f"Workflow file {cwl_workflow} does not exist! Please provide a valid path."
        )

    if not isinstance(script_folder, Path):
        script_folder = Path(script_folder)
    if not script_folder.exists():
        raise ValueError(
            f"Script folder {script_folder} does not exist! Please provide a valid path."
        )

    config_fn = (
        database.input_path / "scenarios" / scenario / f"cwl_config_{scenario}.yml"
    )
    print(f"Saving cwl config to {str(config_fn)}")
    print(f"Workflow file: {str(cwl_workflow)}")
    # Generate cwl template
    cmd = f'cwltool --make-template "{str(cwl_workflow)}" > "{str(config_fn)}"'
    subprocess.run(cmd, shell=True)

    with open(config_fn, "r") as f:
        cwl_config = yaml.load(f, Loader=yaml.FullLoader)

    script_inputs = [key for key in cwl_config if "script" in key]
    for input in script_inputs:
        path = list(script_folder.glob(f"{input.split('_', maxsplit=1)[1]}*"))[0]
        cwl_config[input]["path"] = quoted(str(path))

    cwl_config["scenario"] = scenario
    cwl_config["fa_input_folder"]["path"] = quoted(str(database.input_path))
    cwl_config["fa_static_folder"]["path"] = quoted(str(database.static_path))

    cwl_config["service_directory"]["path"] = quoted(WORFKFLOW_DIR / "oscar_services")
    cwl_config["oscar_output"] = quoted(oscar_output)
    cwl_config["endpoint"] = quoted(oscar_endpoint)
    cwl_config["refreshtoken"] = quoted(oscar_token)

    cwl_config["service_wflow"] = (
        quoted("wflow-interlink") if interlink_offload else quoted("wflow")
    )
    cwl_config["service_sfincs"] = (
        quoted("sfincs-interlink") if interlink_offload else quoted("sfincs")
    )
    cwl_config["service_ra2ce"] = quoted("ra2ce")
    # cwl_config["service_ra2ce"] = (
    #     quoted("ra2ce-interlink") if interlink_offload else quoted("ra2ce")
    # )

    print(f"Write Config file {config_fn} to folder {config_fn}")
    with open(config_fn, "w+") as f:
        yaml.dump(cwl_config, f, default_flow_style=False, sort_keys=True)


def create_setup_workflow_config(
    database_path: Union[str, os.PathLike],
    region: Union[str, os.PathLike, list[dict]],
    oscar_endpoint: str,
    oscar_token: str,
    cwl_workflow: Union[str, os.PathLike] = WORFKFLOW_DIR / "setup_fa_database.cwl",
    script_folder: Union[str, os.PathLike] = SCRIPT_DIR,
):
    """Write config for setup database workflow.

    Parameters
    ----------
    database_path : Union[str, os.PathLike]
        Location of to-be-created workflow
    region_file : Union[str, os.PathLike]
        File defining RoI
    oscar_endpoint : str
        URL of Oscar endpoint
    oscar_token : str
        EGI-SSO refresh token for authentication
    cwl_workflow : Union[str, os.PathLike], optional
        Path to cwl workflow description, by default WORFKFLOW_DIR/"setup_fa_database.cwl"
    script_folder : Union[str, os.PathLike], optional
        Path to folder containing py script being called by workflows, by default SCRIPT_DIR
    """
    if not isinstance(cwl_workflow, Path):
        cwl_workflow = Path(cwl_workflow)
    if not cwl_workflow.exists():
        raise ValueError(
            f"Workflow file {cwl_workflow} does not exist! Please provide a valid path."
        )

    if not isinstance(script_folder, Path):
        script_folder = Path(script_folder)
    if not script_folder.exists():
        raise ValueError(
            f"Script folder {script_folder} does not exist! Please provide a valid path."
        )

    database_root = database_path.parent
    database_name = database_path.name

    database_root.mkdir(parents=True, exist_ok=True)

    if isinstance(region, list):
        try:
            [geom] = region
        except ValueError:
            raise ValueError(
                "region not a singleton list, please provide only one geometry."
            )
        region_file = database_root / f"region_selection_{database_name}.geojson"
        with open(region_file, "w") as f:
            geojson.dump(geom, f)
    else:
        region_file = region

    config_fn = database_root / "cwl_config_setup_database.yml"
    print(f"Saving cwl config to {str(config_fn)}")
    print(f"Workflow file: {str(cwl_workflow)}")
    # Generate cwl template
    cmd = f'cwltool --make-template "{cwl_workflow.as_posix()}" > "{config_fn.as_posix()}"'
    subprocess.run(cmd, shell=True)

    with open(config_fn, "r") as f:
        cwl_config = yaml.load(f, Loader=yaml.FullLoader)

    script_inputs = [key for key in cwl_config if "script" in key]
    for input in script_inputs:
        path = list(script_folder.glob(f"{input.split('_', maxsplit=1)[1]}*"))[0]
        cwl_config[input]["path"] = quoted(str(path))

    cwl_config["region_file"]["path"] = quoted(region_file)
    cwl_config["sf_res"] = 100
    cwl_config["sf_subgrid_pixels"] = 6
    cwl_config["database_name"] = quoted(database_name)
    cwl_config["endpoint"] = quoted(oscar_endpoint)
    cwl_config["refreshtoken"] = quoted(oscar_token)
    cwl_config["oscar_output"] = quoted("output")
    cwl_config["service_ra2ce"] = quoted("ra2ce")
    cwl_config["service_directory"]["path"] = quoted(WORFKFLOW_DIR / "oscar_services")

    print(f"Write Config file {config_fn} to folder {config_fn.parent}")
    with open(config_fn, "w+") as f:
        yaml.dump(cwl_config, f, default_flow_style=False, sort_keys=True)


def run_fa_scenario_workflow(
    database: Union[str, os.PathLike, IDatabase],
    scenario: str,
    debug: bool = False,
) -> None:
    """Execute FloodAdapt scenario.

    Path to CWL workflow description is hardcoded relative to database location.

    Parameters
    ----------
    database : Union[str, os.PathLike, IDatabase]
        FloodAdapt database being used
    scenario : str
        Name of scenario to execute
    """
    if isinstance(database, str) or isinstance(database, Path):
        database, _ = init_scenario(database, scenario)

    database = database.database

    workflow_fn = WORFKFLOW_DIR / "run_fa_scenario.cwl"
    config_fn = (
        database.input_path / "scenarios" / scenario / f"cwl_config_{scenario}.yml"
    )
    cmd_validate = f'cwltool --validate "{str(workflow_fn)}" "{str(config_fn)}"'
    print("Validating workflow")
    print(f"Running {cmd_validate}")
    result = subprocess.run(cmd_validate, shell=True)
    assert result.returncode == 0, "CWL Validation Error, exit workflow execution"

    logfile = (
        database.input_path / "scenarios" / scenario / f"log_workflow_{scenario}.txt"
    )

    if debug:
        cmd = [
            "cwltool",
            "--outdir",
            database.base_path.as_posix(),
            "--cachedir",
            database.base_path.joinpath("cachedir").as_posix(),
            workflow_fn.as_posix(),
            config_fn.as_posix(),
        ]
    else:
        cmd = [
            "cwltool",
            "--outdir",
            database.base_path.as_posix(),
            workflow_fn.as_posix(),
            config_fn.as_posix(),
        ]

    print("Executing workflow")
    print(f"Running {cmd}")
    with open(logfile, "w") as log:
        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while ps.poll() is None:
            line = ps.stdout.readline()
            print(line.strip().decode())
            log.write(line.decode())


def run_setup_database_workflow(
    database_path: Union[str, os.PathLike],
    debug=False,
):
    """Execute database setup workflow.

    Parameters
    ----------
    database_path : Union[str, os.PathLike]
        Location of to-be-created workflow
    debug : bool, optional
        Toggle caching workflow steps for debugging, by default False
    """
    workflow_fn = WORFKFLOW_DIR / "setup_fa_database.cwl"
    config_fn = database_path.parent / "cwl_config_setup_database.yml"

    cmd_validate = f'cwltool --validate "{str(workflow_fn)}" "{str(config_fn)}"'
    print("Validating workflow")
    print(f"Running {cmd_validate}")
    result = subprocess.run(cmd_validate, shell=True)
    assert result.returncode == 0, "CWL Validation Error, exit workflow execution"

    logfile = database_path.parent / "setup_database.log"

    if debug:
        cmd = [
            "cwltool",
            "--outdir",
            database_path.parent.as_posix(),
            "--cachedir",
            (database_path.parent / "cachedir").as_posix(),
            workflow_fn.as_posix(),
            config_fn.as_posix(),
        ]
    else:
        cmd = [
            "cwltool",
            "--outdir",
            database_path.parent.as_posix(),
            workflow_fn.as_posix(),
            config_fn.as_posix(),
        ]

    print("Executing workflow")
    print(f"Running {cmd}")
    with open(logfile, "w") as log:
        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while ps.poll() is None:
            line = ps.stdout.readline()
            print(line.strip().decode())
            log.write(line.decode())
