cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    update_script: File
    run_script: File
    utils_script_docker: File
outputs:
    fa_database_out:
        type: Directory
        outputSource: run_ra2ce/fa_database_out

steps:
    update_ra2ce:
        in:
            fa_database: fa_database
            pyscript: update_script
            scenario: scenario
            utils_script_docker: utils_script_docker
        out:
            [fa_database_out]
        run: ./update_ra2ce.cwl
    run_ra2ce:
        in:
            fa_database: update_ra2ce/fa_database_out
            pyscript: run_script
            scenario: scenario
        out:
            [fa_database_out]
        run: ./run_ra2ce.cwl