cwlVersion: v1.2
class: Workflow

requirements:
    SubworkflowFeatureRequirement: {}

inputs:
    fa_input_folder: Directory
    fa_static_folder: Directory
    scenario: string
    script_init: File
    script_update_wflow_warmup: File
    script_update_wflow_event: File
    script_update_sfincs: File
    script_postprocess_sfincs: File
    script_update_fiat: File
    script_run_fiat: File
    script_postprocess_fiat: File
    script_update_ra2ce: File
    script_construct_output: File
    script_utils_ra2ce_docker: File
    script_oscar: File
    endpoint: string
    refreshtoken: string
    service_wflow: string
    service_sfincs: string
    service_ra2ce: string
    service_directory: Directory
    oscar_output: string

outputs:
    fa_out_dir:
        type: Directory
        outputSource: construct_output/fa_out_dir

steps:
    init_scenario:
        in:
            pyscript: script_init
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            scenario: scenario
        out:
            [output_folder]
        run: ./cwl/init_scenario.cwl
    wflow_warmup:
        in:
            pyscript: script_update_wflow_warmup
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder:  init_scenario/output_folder
            scenario: scenario
        out:
            [warmup_folder]
        run: ./cwl/update_wflow_warmup.cwl
    run_wflow_warmup:
        in:
            pyscript: script_oscar
            filename: wflow_warmup/warmup_folder
            endpoint: endpoint
            refreshtoken: refreshtoken
            service: service_wflow
            service_directory: service_directory
            output: oscar_output
        out:
            [oscar_out]
        run:
            ./cwl/oscar.cwl
    wflow_event:
        in:
            pyscript: script_update_wflow_event
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder: init_scenario/output_folder
            scenario: scenario
            warmup_dir: run_wflow_warmup/oscar_out
        out:
            [wflow_event_folder]
        run: ./cwl/update_wflow_event.cwl
    run_wflow_event:
        in:
            pyscript: script_oscar
            filename: wflow_event/wflow_event_folder
            endpoint: endpoint
            refreshtoken: refreshtoken
            service: service_wflow
            service_directory: service_directory
            output: oscar_output
        out:
            [oscar_out]
        run:
            ./cwl/oscar.cwl
    update_sfincs:
        in:
            pyscript: script_update_sfincs
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder: init_scenario/output_folder
            scenario: scenario
            wflow_dir: run_wflow_event/oscar_out
        out:
            [sfincs_dir]
        run:
            ./cwl/update_sfincs.cwl
    run_sfincs:
        in:
            pyscript: script_oscar
            filename: update_sfincs/sfincs_dir
            endpoint: endpoint
            refreshtoken: refreshtoken
            service: service_sfincs
            service_directory: service_directory
            output: oscar_output
        out:
            [oscar_out]
        run:
            ./cwl/oscar.cwl
    post_sfincs:
        in:
            pyscript: script_postprocess_sfincs
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            scenario: scenario
            sfincs_dir: run_sfincs/oscar_out
        out:
            [floodmap, waterlevel_map]
        run:
            ./cwl/postprocess_sfincs.cwl
    update_fiat:
        in:
            pyscript: script_update_fiat
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder: init_scenario/output_folder
            scenario: scenario
            floodmap: post_sfincs/floodmap
            waterlevel_map: post_sfincs/waterlevel_map
        out:
            [fiat_dir]
        run:
            ./cwl/update_fiat.cwl
    run_fiat:
        in:
            script: script_run_fiat
            fiat_dir: update_fiat/fiat_dir
        out:
            [fiat_out_dir]
        run:
            ./cwl/run_fiat.cwl
    postprocess_fiat:
        in:
            pyscript: script_postprocess_fiat
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder: init_scenario/output_folder
            scenario: scenario
            fiat_dir: run_fiat/fiat_out_dir
        out:
            [fiat_out_dir]
        run:
            ./cwl/postprocess_fiat.cwl
    update_ra2ce:
        in:
            pyscript: script_update_ra2ce
            input_folder: fa_input_folder
            static_folder: fa_static_folder
            output_folder: init_scenario/output_folder
            scenario: scenario
            floodmap: post_sfincs/floodmap
            utils_script_docker: script_utils_ra2ce_docker
        out:
            [ra2ce_dir]
        run:
            ./cwl/update_ra2ce.cwl
    run_ra2ce:
        in:
            pyscript: script_oscar
            filename: update_ra2ce/ra2ce_dir
            endpoint: endpoint
            refreshtoken: refreshtoken
            service: service_ra2ce
            service_directory: service_directory
            output: oscar_output
        out:
            [oscar_out]
        run:
            ./cwl/oscar.cwl
    construct_output:
        in:
            pyscript: script_construct_output
            output_folder: init_scenario/output_folder
            scenario: scenario
            wflow_warmup: run_wflow_warmup/oscar_out
            wflow_event: run_wflow_event/oscar_out
            sfincs_dir: run_sfincs/oscar_out
            fiat_dir: postprocess_fiat/fiat_out_dir
            ra2ce_dir: run_ra2ce/oscar_out
            floodmap: post_sfincs/floodmap
            waterlevels: post_sfincs/waterlevel_map
        out:
            [fa_out_dir]
        run:
            ./cwl/construct_output.cwl