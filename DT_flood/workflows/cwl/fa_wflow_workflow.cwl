cwlVersion: v1.2
class: Workflow

inputs:
    fa_database: Directory
    scenario: string
    # data_catalog: File
    wflow_update_script: File
    oscar_script: File
    endpoint: string
    user: string
    password: string
    service: string
    filename: File
    oscar_service: Directory
    output: Directory
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
            oscar_script: oscar_script
            endpoint: endpoint
            user: user
            password: password
            service: service
            filename: filename
            oscar_service: oscar_service
            output: output
            mode:
                default: "warmup"
        out:
            [fa_database_out]
        run:
            ../cwl_OSCAR/oscar_all/oscar.cwl 
            #./run_wflow.cwl
    run_wflow_event:
        in:
            fa_database: run_wflow_warmup/fa_database_out
            scenario: scenario
            oscar_script: oscar_script
            endpoint: endpoint
            user: user
            password: password
            service: service
            filename: filename
            oscar_service: oscar_service
            output: output
            mode:
                default: "event"
        out:
            [fa_database_out]
        run:
            ../cwl_OSCAR/oscar_all/oscar.cwl 
            #./run_wflow.cwl
