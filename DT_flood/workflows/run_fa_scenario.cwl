cwlVersion: v1.2
class: Workflow

requirements:
    SubworkflowFeatureRequirement: {}

inputs:
    fa_database: Directory
    scenario: string
    script_init: File
    script_update_sfincs: File
    script_arrange: File
    script_update_fiat: File
    script_run_fiat: File

outputs:
    fa_database_out:
        type: Directory
        outputSource: run_fiat/fa_database_out


steps:
    init_scenario:
        in:
            pyscript: script_init
            fa_database: fa_database
            scenario: scenario
        out:
            [fa_database_out]
        run:
            ./cwl/init_fa_scenario.cwl

    run_sfincs:
        in:
            fa_database: init_scenario/fa_database_out
            scenario: scenario
            sfincs_update_script: script_update_sfincs
            arrange_script: script_arrange
        out:
            [fa_database_out]
        run:
            ./cwl/fa_sfincs_workflow_docker.cwl
    update_fiat:
        in:
            fa_database: run_sfincs/fa_database_out
            scenario: scenario
            pyscript: script_update_fiat
        out:
            [fa_database_out]
        run:
            ./cwl/update_fiat.cwl
    run_fiat:
        in:
            fa_database: update_fiat/fa_database_out
            scenario: scenario
            pyscript: script_run_fiat
        out:
            [fa_database_out]
        run:
            ./cwl/run_fiat.cwl

