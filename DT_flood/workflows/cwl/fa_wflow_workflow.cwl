cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    # data_catalog: File
    wflow_update_script: File

outputs:
    fa_database_out:
        type: Directory
        outputSource: run_wflow_event/fa_database_out

steps:
    setup_wflow_warmup:
        in:
            pyscript: wflow_update_script
            fa_database: fa_database
            scenario: scenario
            # data_catalog: data_catalog
            mode:
                default: "warmup"
        out:
            [fa_database_out]
        run:
            ./update_wflow_warump.cwl
    setup_wflow_event:
        in:
            pyscript: wflow_update_script
            fa_database: setup_wflow_warmup/fa_database_out
            scenario: scenario
            # data_catalog: data_catalog
            mode:
                default: "event"
        out:
            [fa_database_out]
        run:
            ./update_wflow_warump.cwl
    run_wflow_warmup:
        in:
            fa_database: setup_wflow_event/fa_database_out
            scenario: scenario
            mode:
                default: "warmup"
        out:
            [fa_database_out]
        run:
            ./run_wflow.cwl
    run_wflow_event:
        in:
            fa_database: run_wflow_warmup/fa_database_out
            scenario: scenario
            mode:
                default: "event"
        out:
            [fa_database_out]
        run:
            ./run_wflow.cwl
