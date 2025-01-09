cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    fiat_update_script: File
    fiat_run_script: File

outputs:
    fa_database_out:
        type: Directory
        outputSource: run_fiat/fa_database_out

steps:
    update_fiat:
        in:
            fa_database: fa_database
            scenario: scenario
            pyscript: fiat_update_script
        out:
            [fa_database_out]
        run:
            ./update_fiat.cwl
    run_fiat:
        in:
            fa_database: update_fiat/fa_database_out
            scenario: scenario
            pyscript: fiat_run_script
        out:
            [fa_database_out]
        run:
            ./run_fiat.cwl