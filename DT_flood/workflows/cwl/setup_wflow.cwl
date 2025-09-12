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
    sfincs_root:
        type: Directory
        inputBinding:
            prefix: "--sfincsroot"
    res:
        type: float?
        inputBinding:
            prefix: "--res"
    basin_data:
        type: string?
        inputBinding:
            prefix: "--basindata"
    hydro_data:
        type: string?
        inputBinding:
            prefix: "--hydrodata"
    river_data:
        type: string?
        inputBinding:
            prefix: "--riverdata"
    lake_data:
        type: string?
        inputBinding:
            prefix: "--lakedata"
    reservoir_data:
        type: string?
        inputBinding:
            prefix: "--reservoirdata"
    lulc_data:
        type: string?
        inputBinding:
            prefix: "--lulcdata"
    lai_data:
        type: string?
        inputBinding:
            prefix: "--laidata"
    soil_data:
        type: string?
        inputBinding:
            prefix: "--soildata"

outputs:
    wflow_dir:
        type: Directory
        outputBinding:
            glob: "wflow"
