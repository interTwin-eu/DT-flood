cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    # model_dir:
    #     type: string
    #     inputBinding:
    #         prefix: "--modeldir"
    region_file:
        type: string
        inputBinding:
            prefix: "--regionfile"
    res:
        type: float
        inputBinding:
            prefix: "--res"
    subgrid_pixels:
        type: int
        inputBinding:
            prefix: "--subgridpixels"
    basin_data:
        type: string?
        inputBinding:
            prefix: "--basindata"
    topo_data:
        type: string?
        inputBinding:
            prefix: "--topodata"
    bathy_data:
        type: string?
        inputBinding:
            prefix: "--bathydata"
    river_data:
        type: string?
        inputBinding:
            prefix: "--riverdata"
    lulc_data:
        type: string?
        inputBinding:
            prefix: "--lulcdata"
    infilt_data:
        type: string?
        inputBinding:
            prefix: "--infiltdata"

outputs:
    sfincs_dir:
        type: Directory
        outputBinding:
            glob: "overland"
    data_dir:
        type: Directory
        outputBinding:
            glob: "data"
