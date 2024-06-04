import os
import subprocess
import yaml
import tomli
from pathlib import Path
from typing import Union

from flood_adapt.object_model.interface.database import IDatabase
from flood_adapt.object_model.interface.scenarios import IScenario

from .fa_scenario_utils import init_scenario, create_scenario


def run_scenario(
        database: Union[str, os.PathLike],
        scenario_name: str,
) -> None:
    
    db, scen_init = init_scenario(database, scenario_name)

    scen_obj = create_scenario(db, scen_init)

    create_workflow_config(db, scen_obj)
    run_fa_scenario_workflow(db, scen_obj)
    


def create_workflow_config(
        database: Union[str, os.PathLike, IDatabase],
        scenario: Union[str, IScenario],
        cwl_workflow: Union[str, os.PathLike] = None,
        script_folder: Union[str, os.PathLike] = None,
        # data_catalog: Union[str, os.PathLike] = Path("/home/wotromp/DestinE_workflows/deltares_data_wsl.yml")
) -> None:
    """Writes Config file for CWL workflow to FloodAdapt database

    Parameters
    ----------
    database : Union[str, os.PathLike, IDatabase]
        FloodAdapt database containing the scenario
    scenario : str
        Name of scenario
    cwl_workflow : Union[str, os.PathLike], optional
        Path to cwl workflow description
    script_folder : Union[str, os.PathLike], optional
        Path to folder containing py script being called by workflows
    data_catalog : Union[str, os.PathLike], optional
        Path to data catalog needed by workflow, by default Path("/home/wotromp/DestinE_workflows/deltares_data_wsl.yml")
    """

    # Parse inputs
    if type(script_folder) is str:
        script_folder = Path(script_folder)
    if type(scenario) is IScenario:
        scenario = scenario.attrs.name
    if type(database) is IDatabase:
        database = database.input_path.parent

    if cwl_workflow is None:
        cwl_workflow = Path(__file__).parents[1]/"workflows"/"run_fa_scenario.cwl"
    else:
        assert Path(cwl_workflow).exists(), "Workflow file does not exist!"

    if script_folder is None:
        script_folder = Path(__file__).parents[1]/"workflows"/"pyscripts"
    else:
        assert Path(script_folder).exists(), "Script folder does not exist!"


    # Check inputs
    # assert Path(data_catalog).exists(), "Data catalog file does not exist!"



    config_fn = database/f"cwl_config_{scenario}.yml"

    # Generate cwl template
    cmd = f"cwltool --make-template {str(cwl_workflow)} > {str(config_fn)}"
    subprocess.run(cmd, shell=True)

    with open(config_fn, 'r') as f:
        cwl_config = yaml.load(f, Loader=yaml.FullLoader)

    script_inputs = [key for key in cwl_config if 'script' in key]
    for input in script_inputs:
        path = list(script_folder.glob(f"{input.split('_', maxsplit=1)[1]}*.py"))[0]
        cwl_config[input]["path"] = str(path)

    cwl_config['scenario'] = scenario
    cwl_config["fa_database"]['path'] = str(database)
    # cwl_config["data_catalog"]['path'] = str(data_catalog)

    print(f"Write Config file {config_fn} to folder {config_fn}")
    with open(config_fn, 'w+') as f:
        yaml.dump(cwl_config, f, default_flow_style=False, sort_keys=True)
    

def run_fa_scenario_workflow(        
        database: Union[str, os.PathLike, IDatabase],
        scenario: Union[str, IScenario],
        ) -> None:
    """Execute FloodAdapt scenario
    Path to CWL workflow description is hardcoded relative to database location

    Parameters
    ----------
    database : Union[str, os.PathLike, IDatabase]
        FloodAdapt database being used
    scenario : Union[str, IScenario]
        Name of scenario to execute
    """    

    if type(database) is IDatabase:
        database = database.input_path.parent
    if type(scenario) is IScenario:
        scenario = scenario.attrs.name

    workflow_fn = Path(__file__).parents[1]/"workflows"/"run_fa_scenario.cwl"
    config_fn = database/f"cwl_config_{scenario}.yml"
    cmd_validate = f"cwltool --validate {str(workflow_fn)} {str(config_fn)}"
    print("Validating workflow")
    print(f"Running {cmd_validate}")
    result = subprocess.run(cmd_validate, shell=True)
    assert result.returncode == 0, "CWL Validation Error, exit workflow execution"


    cmd_run = f"cwltool --outdir {str(database.parent)} --preserve-entire-environment {str(workflow_fn)} {str(config_fn)}"
    print("Executing workflow")
    print(f"Running {cmd_run}")
    subprocess.run(cmd_run, shell=True)
