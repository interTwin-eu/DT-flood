cwlVersion: v1.2
class: Workflow

inputs:
    region_file: File
    script_setup_sfincs: File
    script_setup_wflow: File
    script_setup_fiat: File
    script_setup_ra2ce: File
    script_build_ra2ce: File
    script_oscar: File
    sf_res: float
    sf_subgrid_pixels: int
    endpoint: string
    refreshtoken: string
    service_ra2ce: string
    service_directory: Directory
    oscar_output: string

outputs:
    oscar_out:
        type: Directory
        outputSource: build_ra2ce/oscar_out
    sfincs_dir:
        type: Directory
        outputSource: setup_sfincs/sfincs_dir
    fiat_dir:
        type: Directory
        outputSource: setup_fiat/fiat_dir

steps:
    setup_sfincs:
        in:
            pyscript: script_setup_sfincs
            region_file: region_file
            res: sf_res
            subgrid_pixels: sf_subgrid_pixels
        out:
            [sfincs_dir]
        run: ./cwl/setup_sfincs.cwl
    setup_wflow:
        in:
            pyscript: script_setup_wflow
            region_file: region_file
            sfincs_root: setup_sfincs/sfincs_dir
        out:
            [wflow_dir]
        run: ./cwl/setup_wflow.cwl
    setup_fiat:
        in:
            pyscript: script_setup_fiat
            region_file: region_file
            sfincs_root: setup_sfincs/sfincs_dir
        out:
            [fiat_dir]
        run: ./cwl/setup_fiat.cwl
    setup_ra2ce:
        in:
            pyscript:   script_setup_ra2ce
            region_file: region_file
        out:
            [ra2ce_dir]
        run: ./cwl/setup_ra2ce.cwl
    build_ra2ce:
        in:
            pyscript: script_oscar
            endpoint: endpoint
            refreshtoken: refreshtoken
            service: service_ra2ce
            filename: setup_ra2ce/ra2ce_dir
            service_directory: service_directory
            output: oscar_output
            runscript: script_build_ra2ce
        out:
            [oscar_out]
        run: ./cwl/oscar.cwl
