cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    minio_path: string
    script_init: File
    script_update_wflow: File

outputs: []
    # fa_database_out:
    #     type: Directory
    #     outputSource: run_wflow_warmup/fa_database_out

steps:
    init_scenario:
        in:
            pyscript: script_init
            fa_database: fa_database
            scenario: scenario
        out:
            [fa_database_out]
        run:
            ./init_scenario.cwl
    setup_wflow_warmup:
        in:
            pyscript: script_update_wflow
            fa_database: fa_database
            scenario: scenario
            mode:
                default: "warmup"
        out:
            [fa_database_out]
        run:
            ./update_wflow.cwl
    to_minio:
        in: 
            src: setup_wflow_warmup/fa_database_out
            dest: minio_path
        out: []
        run:
            ./mc_cp.cwl
    # run_wflow_warmup:
    #     in:
    #         fa_database: setup_wflow_warmup/fa_database_out
    #         scenario: scenario
    #         mode:
    #             default: "warmup"
    #     out:
    #         [fa_database_out]
    #     run:
    #         ./run_wflow.cwl