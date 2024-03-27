cwlVersion: v1.2
class: Workflow

requirements:
    SubworkflowFeatureRequirement: {}

inputs:
    fa_database: Directory
    scenario: string
    data_catalog: File
    init_script: File
    wflow_update_script: File
    sfincs_update_script: File
    arrange_script: File
    fiat_update_script: File
    fiat_run_script: File

outputs:
    fa_database:
        type: Directory
        outputSource: run_fiat/fa_database


steps:
    init_scenario:
        in:
            pyscript: init_script
            fa_database: fa_database
            scenario: scenario
        out:
            [fa_database]
        run:
            ./cwl/init_fa_scenario.cwl
    run_wflow:
        in:
            fa_database: init_scenario/fa_database
            scenario: scenario
            data_catalog: data_catalog
            wflow_update_script: wflow_update_script
        out:
            [fa_database]
        run:
            ./cwl/fa_wflow_workflow.cwl

    run_sfincs:
        in:
            fa_database: run_wflow/fa_database
            scenario: scenario
            sfincs_update_script: sfincs_update_script
            arrange_script: arrange_script
        out:
            [fa_database]
        run:
            ./cwl/fa_sfincs_workflow_docker.cwl
    update_fiat:
        in:
            fa_database: run_sfincs/fa_database
            scenario: scenario
            pyscript: fiat_update_script
        out:
            [fa_database]
        run:
            ./cwl/update_fiat.cwl
    run_fiat:
        in:
            fa_database: update_fiat/fa_database
            scenario: scenario
            pyscript: fiat_run_script
        out:
            [fa_database]
        run:
            ./cwl/run_fiat.cwl

