cwlVersion: v1.2
class: CommandLineTool

baseCommand: ["python"]

inputs:
    pyscript:
        type: File
        inputBinding:
            position: -1
    region_file:
        type: File
        inputBinding:
            prefix: "--regionfile"
    res:
        type: float?
        inputBinding:
            prefix: "--res"
    subgrid_pixels:
        type: int?
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
