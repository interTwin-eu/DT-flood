cwlVersion: v1.2
class: Workflow

requirements:
    SubworkflowFeatureRequirement: {}

inputs:
    fa_database: Directory
    scenario: string
    script_init: File
    script_update_sfincs: File
    script_update_sfincs_offshore: File
    script_postprocess_sfincs: File
    script_arrange: File
    script_update_fiat: File
    script_run_fiat: File
    script_postprocess_fiat: File
    script_update_ra2ce: File
    script_run_ra2ce: File
    script_utils_ra2ce_docker: File
    oscar_script: File
    endpoint: string
    user: string
    password: string
    service: string
    filename: Directory
    oscar_service: Directory
    output: Directory
outputs:
    fiat_out:
        type: Directory
        outputSource: run_fiat/fa_database_out
    ra2ce_out:
        type: Directory
        outputSource: run_ra2ce/fa_database_out


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
    run_sfincs_offshore:
        in:
            fa_database: init_scenario/fa_database_out
            scenario: scenario
            sfincs_update_script: script_update_sfincs_offshore
            arrange_script: script_arrange
            mode:
                default: "offshore"
        out:
            [fa_database_out]
        run:
            ./cwl/fa_sfincs_workflow_docker.cwl
    run_sfincs:
        in:
            fa_database: run_sfincs_offshore/fa_database_out
            scenario: scenario
            sfincs_update_script: script_update_sfincs
            sfincs_postprocess_script: script_postprocess_sfincs
            arrange_script: script_arrange
            mode:
                default: "overland"
        out:
            [fa_database_out]
        run:
            ./cwl/fa_sfincs_workflow_docker.cwl
    run_fiat:
        in:
            fa_database: run_sfincs/fa_database_out
            scenario: scenario
            fiat_update_script: script_update_fiat
            fiat_run_script: script_run_fiat
        out:
            [fa_database_out]
        run:
            ./cwl/fa_fiat_workflow.cwl
    run_ra2ce:
        in:
            fa_database: run_sfincs/fa_database_out
            scenario: scenario
            update_script: script_update_ra2ce
            run_script: script_run_ra2ce
            utils_script_docker: script_utils_ra2ce_docker
        out:
            [fa_database_out]
        run:
            ./cwl/run_fiat.cwl
    postprocess_fiat:
        in:
            fa_database: run_fiat/fa_database_out
            scenario: scenario
            pyscript: script_postprocess_fiat
        out:
            [fa_database_out]
        run:
            ./cwl/postprocess_fiat.cwl

