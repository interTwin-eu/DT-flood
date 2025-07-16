cwlVersion: v1.2
class: Workflow

inputs:
    region_file: File
    sf_res: float
    sf_subgrid_pixels: int
    script_setup_sfincs: File

outputs:
    sfincs_dir:
        type: Directory
        outputSource: setup_sfincs/sfincs_dir
    data_dir:
        type: Directory
        outputSource: setup_sfincs/data_dir

steps:
    setup_sfincs:
        in:
            pyscript: script_setup_sfincs
            region_file: region_file
            res: sf_res
            subgrid_pixels: sf_subgrid_pixels
        out:
            [sfincs_dir, data_dir]
        run: cwl/setup_sfincs.cwl
