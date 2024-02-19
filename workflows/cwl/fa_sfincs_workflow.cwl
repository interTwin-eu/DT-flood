cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    sfincs_update_script: File
    sfincs_run_script: File

outputs:
    fa_database:
        type: Directory
        outputSource: run_sfincs/fa_database


steps:
    setup_sfincs:
        in:
            fa_database: fa_database
            scenario: scenario
            pyscript: sfincs_update_script
        out:
            [fa_database]
        run:
            ./update_sfincs.cwl
    run_sfincs:
        in:
            pyscript: sfincs_run_script
            fa_database: setup_sfincs/fa_database
            scenario: scenario
        out:
            [fa_database]
        run:
            ./run_sfincs.cwl